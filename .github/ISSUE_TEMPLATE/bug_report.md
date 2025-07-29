---
name: Bug report
about: Create a report to help us improve
title: '[BUG] '
labels: ['bug', 'needs-triage']
assignees: ''
---

## 🐛 Bug Description

A clear and concise description of what the bug is.

## 🔄 Steps to Reproduce

1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

## ✅ Expected Behavior

A clear and concise description of what you expected to happen.

## ❌ Actual Behavior

A clear and concise description of what actually happened.

## 📸 Screenshots

If applicable, add screenshots to help explain your problem.

## 🖥️ Environment

**OS:** [e.g. Ubuntu 22.04, macOS 14.0, Windows 11]
**Python Version:** [e.g. 3.12.0]
**Package Version:** [e.g. 0.1.0]
**Service:** [e.g. elasticsearch, mysql, postgresql]

## 📋 Additional Context

Add any other context about the problem here, such as:
- Configuration files
- Log files
- Error messages
- Related issues

## 🔧 Configuration

```yaml
# Your configuration (remove sensitive information)
elasticsearch:
  hosts: ["http://localhost:9200"]
  repository_name: "s3_backup"
  indices: ["*"]

s3:
  bucket_name: "my-bucket"
  region: "us-east-1"
```

## 📝 Error Logs

```
# Paste relevant error logs here
[ERROR] 2024-01-15 10:30:00 - Failed to create snapshot
Traceback (most recent call last):
  File "main.py", line 45, in snapshot()
    raise Exception("Snapshot failed")
Exception: Snapshot failed
```

## 🎯 Checklist

- [ ] I have searched existing issues to avoid duplicates
- [ ] I have provided all required information
- [ ] I have included error logs and stack traces
- [ ] I have specified my environment details
- [ ] I have removed sensitive information from logs/configs