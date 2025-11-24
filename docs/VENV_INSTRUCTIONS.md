# 虚拟环境（Virtual Environment）使用说明

以下示例假设在仓库根目录运行脚本。

PowerShell（Windows）

- 创建默认虚拟环境 `.venv`：

  ```powershell
  .\create_venv.ps1
  ```

- 指定名字和 Python 可执行文件（例如使用 `python3.11`）：

  ```powershell
  .\create_venv.ps1 -Name myenv -Python python3.11
  ```

- 强制重建已存在的虚拟环境：

  ```powershell
  .\create_venv.ps1 -Name .venv -Recreate
  ```

如果 PowerShell 的执行策略阻止脚本运行，可以临时允许并运行：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force; .\create_venv.ps1
```

# 常见问题

- 如果提示找不到 `python`，请确认 Python 已安装并在系统 PATH 中，或在脚本中显式传入 Python 可执行路径。
- 在 Windows 上运行 PowerShell 脚本可能受执行策略影响，使用上文示例的 `Set-ExecutionPolicy` 命令临时允许执行。
