"""Main CLI entry point for the backup toolkit."""

import asyncio
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from core.snapshot import ElasticsearchSnapshot
from core.restore import ElasticsearchRestore
from core.rotation import SnapshotRotation
from models.config import SnapshotConfig
from utils.config_loader import (
    load_config_from_file,
    load_config_from_env,
    save_sample_config,
)
from utils.logging import setup_logging, get_logger

console = Console()
logger = get_logger(__name__)


@click.group()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file (JSON, YAML, or .env)",
)
@click.option(
    "--log-level",
    default="INFO",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
    help="Logging level",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.pass_context
def cli(
    ctx: click.Context, config: Optional[Path], log_level: str, verbose: bool
) -> None:
    """PlanLX Elasticsearch Snapshot Kit - 快照和恢复Elasticsearch数据到S3。"""
    # Setup logging
    if verbose:
        log_level = "DEBUG"
    setup_logging(level=log_level)

    # Load configuration (only for commands that need it)
    ctx.obj = None
    if config:
        try:
            ctx.obj = load_config_from_file(config)
        except Exception as e:
            console.print(f"[red]配置文件加载失败: {e}[/red]")
            sys.exit(1)
    else:
        # 如果没有提供配置文件，尝试从环境变量加载
        try:
            ctx.obj = load_config_from_env()
        except Exception as e:
            console.print(f"[yellow]环境变量配置加载失败: {e}[/yellow]")
            console.print("[yellow]请设置必要的环境变量或使用 --config 参数指定配置文件[/yellow]")
            # 不退出，让命令自己处理配置缺失的情况


@cli.command()
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default="config.yaml",
    help="输出配置文件路径",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["yaml", "json"]),
    default="yaml",
    help="配置文件格式",
)
def init(output: Path, output_format: str) -> None:
    """创建示例配置文件。"""
    try:
        save_sample_config(output, output_format)
        console.print(f"[green]示例配置文件已创建: {output}[/green]")
        console.print("请根据您的环境更新配置文件中的值。")
    except Exception as e:
        console.print(f"[red]创建配置文件失败: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.pass_obj
def snapshot(config: Optional[SnapshotConfig]) -> None:
    """从源Elasticsearch集群创建快照到S3。"""
    if config is None:
        console.print("[red]错误: 未找到配置信息[/red]")
        console.print("[yellow]请设置环境变量或使用 --config 参数指定配置文件[/yellow]")
        console.print("\n[bold]必需的环境变量:[/bold]")
        console.print("  SNAPSHOT_HOSTS - Elasticsearch 集群地址")
        console.print("  AWS_ACCESS_KEY_ID - AWS 访问密钥")
        console.print("  AWS_SECRET_ACCESS_KEY - AWS 秘密密钥")
        console.print("  S3_BUCKET_NAME - S3 存储桶名称")
        console.print("\n[bold]示例:[/bold]")
        console.print("  export SNAPSHOT_HOSTS=http://localhost:9200")
        console.print("  export AWS_ACCESS_KEY_ID=your-key")
        console.print("  export AWS_SECRET_ACCESS_KEY=your-secret")
        console.print("  export S3_BUCKET_NAME=my-bucket")
        console.print("  uv run python main.py snapshot")
        sys.exit(1)
    
    console.print(
        Panel.fit(
            "[bold blue]开始快照操作[/bold blue]\n"
            f"快照集群: {config.snapshot_hosts_list}\n"
            f"索引: {config.indices_list}\n"
            f"S3存储桶: {config.bucket_name}",
            title="快照信息",
        )
    )

    async def run_snapshot() -> None:
        try:
            snapshot_handler = ElasticsearchSnapshot(config)
            snapshot_name = await snapshot_handler.snapshot()

            console.print(f"[green]快照完成! 快照名称: {snapshot_name}[/green]")

        except Exception as e:
            logger.error(f"快照失败: {e}")
            console.print(f"[red]快照失败: {e}[/red]")
            sys.exit(1)

    asyncio.run(run_snapshot())


@cli.command()
@click.argument("snapshot_name")
@click.pass_obj
def restore(config: SnapshotConfig, snapshot_name: str) -> None:
    """从S3快照恢复到目标Elasticsearch集群。"""
    console.print(
        Panel.fit(
            f"[bold blue]开始恢复操作[/bold blue]\n"
            f"恢复集群: {config.restore_hosts_list}\n"
            f"快照名称: {snapshot_name}\n"
            f"索引: {config.indices_list}\n"
            f"S3存储桶: {config.bucket_name}",
            title="恢复信息",
        )
    )

    async def run_restore() -> None:
        try:
            restore_handler = ElasticsearchRestore(config)
            await restore_handler.restore(snapshot_name)

            console.print(f"[green]恢复完成! 快照: {snapshot_name}[/green]")

        except Exception as e:
            logger.error(f"恢复失败: {e}")
            console.print(f"[red]恢复失败: {e}[/red]")
            sys.exit(1)

    asyncio.run(run_restore())


@cli.command()
@click.pass_obj
def list_snapshots(config: SnapshotConfig) -> None:
    """列出S3存储库中的所有快照。"""

    async def run_list() -> None:
        try:
            restore_handler = ElasticsearchRestore(config)
            await restore_handler.connect()
            await restore_handler.create_repository()

            snapshots = await restore_handler.list_snapshots()

            if not snapshots:
                console.print("[yellow]未找到快照[/yellow]")
                return

            # Create table
            table = Table(title=f"快照列表 - {config.repository_name}")
            table.add_column("快照名称", style="cyan")
            table.add_column("状态", style="green")
            table.add_column("开始时间", style="yellow")
            table.add_column("结束时间", style="yellow")
            table.add_column("索引数量", style="blue")

            for snapshot in snapshots:
                state = snapshot.get("state", "UNKNOWN")
                start_time = snapshot.get("start_time", "")
                end_time = snapshot.get("end_time", "")
                indices = len(snapshot.get("indices", []))

                # Format timestamps
                if start_time:
                    start_time = start_time.split("T")[0]  # Just the date
                if end_time:
                    end_time = end_time.split("T")[0]  # Just the date

                table.add_row(
                    snapshot.get("snapshot", "UNKNOWN"),
                    state,
                    start_time,
                    end_time,
                    str(indices),
                )

            console.print(table)

        except Exception as e:
            logger.error(f"列出快照失败: {e}")
            console.print(f"[red]列出快照失败: {e}[/red]")
            sys.exit(1)
        finally:
            await restore_handler.close()

    asyncio.run(run_list())


@cli.command()
@click.option(
    "--max-snapshots",
    default=10,
    type=int,
    help="Maximum number of snapshots to keep",
)
@click.option(
    "--max-age-days",
    default=30,
    type=int,
    help="Maximum age of snapshots in days",
)
@click.option(
    "--keep-successful-only",
    default=True,
    type=bool,
    help="Keep only successful snapshots",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be deleted without actually deleting",
)
@click.pass_obj
def rotate(
    config: SnapshotConfig,
    max_snapshots: int,
    max_age_days: int,
    keep_successful_only: bool,
    dry_run: bool,
) -> None:
    """轮转和清理旧的快照。"""
    console.print(
        Panel.fit(
            f"[bold blue]开始快照轮转操作[/bold blue]\n"
            f"集群: {config.snapshot_hosts_list}\n"
            f"存储库: {config.repository_name}\n"
            f"最大快照数: {max_snapshots}\n"
            f"最大保留天数: {max_age_days}\n"
            f"仅保留成功快照: {keep_successful_only}\n"
            f"模拟运行: {dry_run}",
            title="轮转信息",
        )
    )

    async def run_rotation() -> None:
        try:
            rotation_handler = SnapshotRotation(config)
            await rotation_handler.connect()
            await rotation_handler.create_repository()

            if dry_run:
                # 模拟运行，只显示将要删除的快照
                snapshots = await rotation_handler.list_snapshots()
                valid_snapshots = []
                
                for snapshot in snapshots:
                    snapshot_name = snapshot.get("snapshot", "")
                    state = snapshot.get("state", "")
                    
                    if keep_successful_only and state != "SUCCESS":
                        continue
                    
                    snapshot_date = rotation_handler.parse_snapshot_date(snapshot_name)
                    if snapshot_date is None:
                        continue
                    
                    valid_snapshots.append({
                        "name": snapshot_name,
                        "date": snapshot_date,
                        "state": state,
                    })

                valid_snapshots.sort(key=lambda x: x["date"], reverse=True)
                cutoff_date = datetime.now() - timedelta(days=max_age_days)

                snapshots_to_delete = []
                snapshots_to_keep = []

                for i, snapshot in enumerate(valid_snapshots):
                    should_delete = False
                    reason = ""

                    if i >= max_snapshots:
                        should_delete = True
                        reason = f"超过最大快照数限制 ({max_snapshots})"
                    elif snapshot["date"] < cutoff_date:
                        should_delete = True
                        reason = f"超过 {max_age_days} 天"

                    if should_delete:
                        snapshots_to_delete.append({
                            "name": snapshot["name"],
                            "date": snapshot["date"],
                            "reason": reason,
                        })
                    else:
                        snapshots_to_keep.append({
                            "name": snapshot["name"],
                            "date": snapshot["date"],
                        })

                # 显示结果
                if snapshots_to_delete:
                    console.print(f"[yellow]将要删除 {len(snapshots_to_delete)} 个快照:[/yellow]")
                    for snapshot in snapshots_to_delete:
                        console.print(f"  - {snapshot['name']} ({snapshot['date'].strftime('%Y-%m-%d %H:%M:%S')}) - {snapshot['reason']}")
                else:
                    console.print("[green]没有需要删除的快照[/green]")

                if snapshots_to_keep:
                    console.print(f"[green]将保留 {len(snapshots_to_keep)} 个快照:[/green]")
                    for snapshot in snapshots_to_keep:
                        console.print(f"  - {snapshot['name']} ({snapshot['date'].strftime('%Y-%m-%d %H:%M:%S')})")

            else:
                # 实际执行轮转
                result = await rotation_handler.rotate_snapshots(
                    max_snapshots=max_snapshots,
                    max_age_days=max_age_days,
                    keep_successful_only=keep_successful_only,
                )

                # 显示结果
                if result["deleted"]:
                    console.print(f"[red]已删除 {result['total_deleted']} 个快照:[/red]")
                    for snapshot in result["deleted"]:
                        console.print(f"  - {snapshot['name']} ({snapshot['date'].strftime('%Y-%m-%d %H:%M:%S')}) - {snapshot['reason']}")
                else:
                    console.print("[green]没有删除任何快照[/green]")

                if result["kept"]:
                    console.print(f"[green]保留 {result['total_kept']} 个快照:[/green]")
                    for snapshot in result["kept"]:
                        console.print(f"  - {snapshot['name']} ({snapshot['date'].strftime('%Y-%m-%d %H:%M:%S')})")

        except Exception as e:
            logger.error(f"轮转失败: {e}")
            console.print(f"[red]轮转失败: {e}[/red]")
            sys.exit(1)
        finally:
            await rotation_handler.close()

    asyncio.run(run_rotation())


@cli.command()
@click.argument("snapshot_names", nargs=-1)
@click.option(
    "--all",
    is_flag=True,
    help="Delete all snapshots in the repository",
)
@click.option(
    "--pattern",
    help="Delete snapshots matching the pattern (e.g., 'snapshot_2025_07_*')",
)
@click.option(
    "--older-than",
    help="Delete snapshots older than specified date (YYYY-MM-DD format)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be deleted without actually deleting",
)
@click.option(
    "--force",
    is_flag=True,
    help="Force deletion without confirmation",
)
@click.pass_obj
def cleanup(
    config: SnapshotConfig,
    snapshot_names: tuple,
    all: bool,
    pattern: str,
    older_than: str,
    dry_run: bool,
    force: bool,
) -> None:
    """清理指定的快照。"""
    
    # 验证参数
    if not snapshot_names and not all and not pattern and not older_than:
        console.print("[red]错误: 必须指定要清理的快照名称、--all、--pattern 或 --older-than 参数[/red]")
        sys.exit(1)
    
    if all and (snapshot_names or pattern or older_than):
        console.print("[red]错误: --all 参数不能与其他参数同时使用[/red]")
        sys.exit(1)

    console.print(
        Panel.fit(
            f"[bold blue]开始快照清理操作[/bold blue]\n"
            f"集群: {config.snapshot_hosts_list}\n"
            f"存储库: {config.repository_name}\n"
            f"指定快照: {snapshot_names if snapshot_names else '无'}\n"
            f"清理所有: {all}\n"
            f"模式匹配: {pattern if pattern else '无'}\n"
            f"早于日期: {older_than if older_than else '无'}\n"
            f"模拟运行: {dry_run}\n"
            f"强制删除: {force}",
            title="清理信息",
        )
    )

    async def run_cleanup() -> None:
        try:
            from core.rotation import SnapshotRotation
            import re
            from datetime import datetime
            
            cleanup_handler = SnapshotRotation(config)
            await cleanup_handler.connect()
            await cleanup_handler.create_repository()

            # 获取所有快照
            all_snapshots = await cleanup_handler.list_snapshots()
            if not all_snapshots:
                console.print("[yellow]存储库中没有快照[/yellow]")
                return

            # 确定要删除的快照
            snapshots_to_delete = []
            
            if all:
                # 删除所有快照
                snapshots_to_delete = [s.get("snapshot", "") for s in all_snapshots]
                console.print(f"[yellow]将要删除所有 {len(snapshots_to_delete)} 个快照[/yellow]")
                
            elif snapshot_names:
                # 删除指定的快照
                existing_snapshots = [s.get("snapshot", "") for s in all_snapshots]
                for name in snapshot_names:
                    if name in existing_snapshots:
                        snapshots_to_delete.append(name)
                    else:
                        console.print(f"[yellow]警告: 快照 '{name}' 不存在[/yellow]")
                        
            elif pattern:
                # 根据模式删除快照
                existing_snapshots = [s.get("snapshot", "") for s in all_snapshots]
                try:
                    pattern_regex = re.compile(pattern.replace("*", ".*"))
                    for snapshot in existing_snapshots:
                        if pattern_regex.match(snapshot):
                            snapshots_to_delete.append(snapshot)
                except re.error as e:
                    console.print(f"[red]错误: 无效的模式 '{pattern}': {e}[/red]")
                    return
                    
            elif older_than:
                # 删除早于指定日期的快照
                try:
                    cutoff_date = datetime.strptime(older_than, "%Y-%m-%d")
                    for snapshot in all_snapshots:
                        snapshot_name = snapshot.get("snapshot", "")
                        snapshot_date = cleanup_handler.parse_snapshot_date(snapshot_name)
                        if snapshot_date and snapshot_date.date() < cutoff_date.date():
                            snapshots_to_delete.append(snapshot_name)
                except ValueError as e:
                    console.print(f"[red]错误: 无效的日期格式 '{older_than}': {e}[/red]")
                    return

            if not snapshots_to_delete:
                console.print("[green]没有需要删除的快照[/green]")
                return

            # 显示将要删除的快照
            console.print(f"[yellow]将要删除 {len(snapshots_to_delete)} 个快照:[/yellow]")
            for snapshot in snapshots_to_delete:
                console.print(f"  - {snapshot}")

            # 确认删除
            if not force and not dry_run:
                confirm = input("\n确认删除这些快照吗? (y/N): ")
                if confirm.lower() not in ['y', 'yes']:
                    console.print("[yellow]操作已取消[/yellow]")
                    return

            if dry_run:
                console.print("[green]模拟运行完成，没有实际删除任何快照[/green]")
                return

            # 执行删除
            deleted_count = 0
            failed_count = 0
            
            for snapshot in snapshots_to_delete:
                try:
                    await cleanup_handler.delete_snapshot(snapshot)
                    deleted_count += 1
                    console.print(f"[green]✓ 已删除: {snapshot}[/green]")
                except Exception as e:
                    failed_count += 1
                    console.print(f"[red]✗ 删除失败: {snapshot} - {e}[/red]")

            # 显示结果
            console.print(f"\n[bold]清理完成:[/bold]")
            console.print(f"[green]成功删除: {deleted_count} 个快照[/green]")
            if failed_count > 0:
                console.print(f"[red]删除失败: {failed_count} 个快照[/red]")

        except Exception as e:
            logger.error(f"清理失败: {e}")
            console.print(f"[red]清理失败: {e}[/red]")
            sys.exit(1)
        finally:
            await cleanup_handler.close()

    asyncio.run(run_cleanup())


@cli.command()
@click.argument("snapshot_name")
@click.pass_obj
def status(config: SnapshotConfig, snapshot_name: str) -> None:
    """获取指定快照的状态信息。"""

    async def run_status() -> None:
        try:
            restore_handler = ElasticsearchRestore(config)
            await restore_handler.connect()
            await restore_handler.create_s3_repository()

            status_info = await restore_handler.get_snapshot_status(snapshot_name)

            if not status_info:
                console.print(f"[yellow]快照 '{snapshot_name}' 未找到[/yellow]")
                return

            # Display status information
            console.print(
                Panel.fit(
                    f"[bold]快照状态信息[/bold]\n"
                    f"名称: {snapshot_name}\n"
                    f"状态: {status_info.get('state', 'UNKNOWN')}\n"
                    f"开始时间: {status_info.get('start_time', 'N/A')}\n"
                    f"结束时间: {status_info.get('end_time', 'N/A')}\n"
                    f"索引: {', '.join(status_info.get('indices', []))}",
                    title="状态详情",
                )
            )

        except Exception as e:
            logger.error(f"获取状态失败: {e}")
            console.print(f"[red]获取状态失败: {e}[/red]")
            sys.exit(1)
        finally:
            await restore_handler.close()

    asyncio.run(run_status())


def main() -> None:
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
