---
title: 树莓派上的 Switch 密钥
parent: Hardware and setup
nav_order: 2
---

# 在树莓派上安装 Switch 密钥

`prod.keys` 保存着用户自己 Switch 的密钥，实时 LDN 主机需要它。切勿将其提交到仓库、粘贴进配置、写入抓包文件，或把桌面端的虚拟环境复制到树莓派；部署过程从不会传输它。它应放在 `/home/PI_USER/.switch/prod.keys`，树莓派上被忽略的 `config/host.local.toml` 会指定该绝对路径，因为主机会以 `sudo` 运行，`~` 不会解析为登录账户：

```toml
[ldn]
keys_path = "/home/PI_USER/.switch/prod.keys"
```

## 在树莓派本地安装

以树莓派登录用户的身份运行安装脚本（在 `sudo` 下它会以 `$SUDO_USER` 重新启动）。它会以 `0700` 权限创建 `~/.switch`，以 `0600` 权限安装该文件，全程不显示其内容；再次运行时会保留相同的文件并修复其权限。源文件必须是绝对路径下的常规文件，且登录用户可读：

```bash
cd ~/pokeldn
./scripts/install_switch_keys.sh --source /absolute/path/to/prod.keys
```

`--stdin` 通过 SSH 流式传入密钥，不产生中转副本：

```bash
# On the desktop; pi-ldn is your SSH alias.
ssh pi-ldn 'cd ~/pokeldn && ./scripts/install_switch_keys.sh --stdin' < "$HOME/.switch/prod.keys"
```

## 通过 SSH 别名使用 SCP

在私有目录中中转，绝不能使用 `/tmp` 这类共享目录，并在之后删除副本（`scp -p` 会保留本地权限）：

```bash
# On the desktop.
ssh pi-ldn 'install -d -m 700 "$HOME/.frlg-ldn-provision"'
scp -p "$HOME/.switch/prod.keys" pi-ldn:.frlg-ldn-provision/prod.keys
ssh pi-ldn 'cd ~/pokeldn && \
  ./scripts/install_switch_keys.sh --source "$HOME/.frlg-ldn-provision/prod.keys" && \
  rm -f "$HOME/.frlg-ldn-provision/prod.keys" && \
  rmdir "$HOME/.frlg-ldn-provision"'
```

验证上述任一方法：

```bash
ssh pi-ldn 'stat -c "%a %U %n" "$HOME/.switch" "$HOME/.switch/prod.keys"'
# Expected: 700 PI_USER /home/PI_USER/.switch
#           600 PI_USER /home/PI_USER/.switch/prod.keys
```
