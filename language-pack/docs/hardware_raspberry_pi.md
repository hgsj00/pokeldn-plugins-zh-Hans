---
title: 树莓派主机
parent: Hardware and setup
nav_order: 4
---

# 树莓派 4 神秘礼物主机

一台 64 位树莓派 4 搭配 TP-Link Archer T3U / AC1300（`2357:012d`、`rtw88_8822bu`）来主持神秘礼物。打过补丁的 LDN 实现位于 `vendor/LDN`；切勿在树莓派上安装未打补丁的 PyPI 包。适配器的内核设置见 [适配器](hardware_adapters.md)。

部署通过 SSH 别名把已提交的 Git 对象推送到树莓派上的裸仓库，不经过 GitHub，不使用 `rsync`，也不包含被忽略的文件（参考仓库、`.venv`、抓包、宝可梦文件、Switch 密钥）。

## 首次部署

在桌面上，从一个已提交的检出目录出发，指定 SSH 别名与树莓派登录用户：

```bash
./scripts/deploy_pi.sh --host pi-ldn --user PI_USER
```

`deploy_pi.sh` 会拒绝有未提交改动的桌面检出，运行配置与文档测试，必要时创建 `/home/PI_USER/repos/pokeldn.git`，把当前提交推送到它的 `deploy` 分支，并创建或快进 `/home/PI_USER/pokeldn`。它从不强制重置，并会拒绝树莓派上存在未提交文件的检出。若 SSH 别名已指明远程用户，则改为给出路径：

```bash
./scripts/deploy_pi.sh --host pi-ldn \
  --path /home/PI_USER/pokeldn \
  --repo /home/PI_USER/repos/pokeldn.git
```

然后初始化树莓派：

```bash
ssh pi-ldn
cd ~/pokeldn
./scripts/setup_pi.sh
```

`setup_pi.sh` 需要 64 位 Raspberry Pi OS（`aarch64`）和 Python 3.11 或更新版本（Bookworm 为 3.11，Trixie 为 3.13）。它依据 `requirements.txt` 构建虚拟环境，安装系统工具（`--no-apt` 可跳过），并把 `ldnclient`、`ldn`、`ldn-mon` 和 `ldn-tap` 从 NetworkManager 中排除（`--no-networkmanager` 可跳过）。请让 SSH 走以太网或内置 Wi-Fi：主持会独占 TP-Link 适配器。

## 配置与 Switch 密钥

仓库跟踪的 `config/host.toml` 就是 TP-Link 的实机配置档：

```toml
[host]
live = true
skip_encryption = true
accept_decrypted_ccmp = true

[ldn]
phy = "auto"
```

被忽略的 `config/host.local.toml` 保存密钥的绝对路径（主机会以 `sudo` 运行）；如何安装 `prod.keys` 见 [树莓派上的 Switch 密钥](hardware_switch_keys.md)。

## 验证与运行

插好 TP-Link 适配器后：

```bash
cd ~/pokeldn
./scripts/preflight_pi.sh
./scripts/run_mystery_gift.sh
```

预检是只读的。它会检查 Python 与随仓库附带的 LDN 包，加载 `config/host.toml` 以及可选的 `config/host.local.toml`，检查 TP-Link 的 USB id 与 `rtw88_8822bu`、AP 与监听模式支持、NetworkManager 排除项，以及密钥文件是否为 `0600` 模式。它会拒绝禁用 `skip_encryption` 或 `accept_decrypted_ccmp` 的 TP-Link 调用，通过 `run_mystery_gift.sh` 传入的参数也包括在内。它会自行添加 Debian 的 `sbin` 路径，因此在 shell 中和通过单行 SSH 命令执行时行为一致。

`run_mystery_gift.sh` 会先运行一次预检，随后监管短时运行的 root 主机进程，每个进程带随机的 TID/SID，并在一次投递、一次失败尝试，或五分钟内没有 Switch 加入或 Pia/RFU 流量之后重启。按一次 Ctrl-C 即可停止。它总是传入 `--end-on-success`（在投递后的关闭之后再结束）和 `--idle-timeout 300`（在无 Switch 流量达到该秒数后结束），并自行掌控 `--id`，因此保存下来的 `--id` 无法复用旧身份。其余所有 `bin/frlg_mg_host.py` 选项都会原样转发；`--help` 和 `--print-effective-config` 既不需要预检也不需要 root。

每次完成加入的尝试都会追加到被忽略的按日账本 `logs/mystery-gift-attempts-YYYY-MM-DD.csv`，其列包括 `attempt`、`received_result`（仅当发送了神秘卡片或印章时为 `true`）、`time`、`trainer_name`、`trainer_ot`（来自 Switch 的 LinkPlayer 区块的名字与五位训练家 ID，若尝试在此之前失败则为空）。`bin/frlg_mg_host.py --attempt-log-dir logs` 会写入同一份账本。

活动控制项：`--gift`、`--flag-id`、`--verbose`、`--capture`、`--ot`、`--version`、`--id`。`--client-ready-idle-frames N` 是用于硬件测试的时序诊断项；其他情况下请勿设置。`--make-artifact` 会在 `artifacts/` 下写出确定性的 `.ram.lst` 清单（`--artifact-dir DIR` 可改变目标位置）：其中包含编译后的 RAM 脚本字节、反汇编指令、校验和、分支与消息目的地，以及投递阶段的摘要；`--no-make-artifact` 可在保存的命令中禁用它。

```bash
./scripts/run_mystery_gift.sh --gift solrock-stamp --client-ready-idle-frames 45 \
  --capture solrock-45.jsonl
./scripts/run_mystery_gift.sh --gift worlds-xp --make-artifact
```

除非在诊断其他硬件，否则请让 `--phy`、`--adapter`、`--skip-encryption` 和 `--accept-decrypted-ccmp` 保持 TP-Link 的默认值。对于 ALFA `mt76x0u`，请传入它当前的 PHY（`iw dev`；重新插拔后会变化）和 `--no-accept-decrypted-ccmp`；随后预检会检查该 PHY 的 AP 与监听模式，以及 `mt76x0u` 的 CCMP 配置档。

### 使用自定义 AP 驱动的 MT7601U 适配器

原版 `mt7601u` 驱动没有 AP 模式。主持需要固定版本的 `mt7601u-ap` DKMS 模块（`vendor/mt7601u-ap-1.0`），且必须在树莓派上针对其 ARM64 内核构建；切勿复制桌面机上构建的 `.ko`。在桌面上：

```bash
./scripts/deploy_pi.sh --host pi-ldn --user PI_USER --install-mt7601u-ap
```

或者在树莓派上：

```bash
cd ~/pokeldn
./scripts/setup_pi.sh --install-mt7601u-ap --no-networkmanager
```

这会安装 `dkms` 和 `linux-headers-rpi-v8`，并为每个已安装且带有匹配头文件的内核注册该模块（APT 可能在重启前装入更新的内核）；若正在运行的内核没有匹配的头文件，它会停止。重新插拔适配器（或重启），从 `iw dev` 读取其 PHY，并以 `--phy phyN --no-accept-decrypted-ccmp` 运行。预检会确认已加载的 `mt7601u` 来自 `updates/dkms`，并具备 AP 与监听模式。

## 部署改动

在桌面上提交，然后再次运行 `./scripts/deploy_pi.sh --host pi-ldn --user PI_USER`。它只对代码做快进；当依赖文件或 `vendor/LDN` 发生变化时，树莓派会刷新其虚拟环境。在树莓派上执行 `./scripts/update_pi.sh` 可在手动推送后更新。切勿在树莓派上编辑被跟踪的文件；请让 `config/host.local.toml`、密钥和抓包只留在树莓派本地并被忽略。
