---
title: "True Deep Sleep: Achieving Suspend-Then-Hibernate on Kubuntu"
date: 2026-06-14T10:03:56.696Z
description: "A complete guide to forcing hardware S3 deep sleep, configuring hibernation, and bypassing KDE PowerDevil for reliable suspend-then-hibernate on Kubuntu with Lenovo ThinkPads."
draft: false
showAuthor: true
showReadingTime: true
showFeatureImage: true
---

Modern Linux distributions often default to `s2idle` (Modern Standby), which keeps the CPU in a shallow low-power state rather than fully powering down components. On laptops like Lenovo ThinkPads, this can result in significant battery drain while the lid is closed.

Furthermore, configuring a proper "Suspend-Then-Hibernate" workflow — where the laptop enters S3 sleep briefly for instant-wake, but eventually hibernates to save battery — often conflicts with desktop environment power managers like KDE's PowerDevil.

This guide covers the complete configuration to force true hardware-level S3 deep sleep, enable proper NVMe power savings during idle, and bypass KDE to achieve reliable suspend-then-hibernate.

## Prerequisites

1. **BIOS/UEFI Configuration:** Ensure your Sleep State is set to **Linux S3** (not Windows 10/Modern Standby). On ThinkPads, this is found under **Config → Power → Sleep State**.
2. **Secure Boot:** Must be **Disabled**. The kernel's Lockdown Mode (enforced when Secure Boot is active) prevents writing RAM contents to disk, which blocks hibernation entirely.

---

## Step 1: Prepare the Swapfile for Hibernation

To hibernate, the kernel writes the contents of RAM to swap. Your swapfile must be at least as large as your physical RAM — slightly larger is recommended to account for memory compression overhead.

Create and initialize the swapfile (adjust the size to match your RAM — this example uses 18G for a 16GB system):

```bash
sudo fallocate -l 18G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

> **Btrfs users:** `fallocate` creates files with holes on Btrfs, and the kernel will refuse to use them for hibernation. Use `dd` instead:
> ```bash
> sudo dd if=/dev/zero of=/swapfile bs=1M count=18432 status=progress
> ```

Make it permanent by adding it to `/etc/fstab`:

```bash
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

Next, gather the **UUID** of your root partition and the physical **offset** of your swapfile. The kernel needs both to locate the swapfile on disk during resume.

```bash
# Get the UUID of the partition containing /swapfile
findmnt -no UUID -T /swapfile

# Get the physical offset
sudo filefrag -v /swapfile | awk 'NR==4 {print $4}' | tr -d '.'
```

Note down both values — you will need them in the next step.

---

## Step 2: Configure GRUB (Boot Parameters)

The kernel needs to know where to find the hibernation image on resume. We pass the resume device and offset through GRUB.

Edit the GRUB configuration:

```bash
sudo nano /etc/default/grub
```

Update the `GRUB_CMDLINE_LINUX_DEFAULT` line (replace the UUID and offset with your own values from Step 1):

```text
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash pcie_aspm=force resume=UUID=YOUR-UUID-HERE resume_offset=YOUR-OFFSET-HERE"
```

### What each parameter does

| Parameter | Purpose |
|---|---|
| `pcie_aspm=force` | Forces Active State Power Management on PCIe devices. Some BIOSes disable ASPM even when the hardware supports it — this overrides that. Reduces idle power draw from NVMe, Wi-Fi, and other PCIe peripherals. |
| `resume=UUID=...` | Tells the kernel which partition holds the swapfile containing the hibernation image. |
| `resume_offset=...` | The physical block offset of the swapfile on that partition, so the kernel can locate it without mounting the filesystem. |

> **Intel-only option:** If you are on an Intel system and want to be explicit about CPU C-state depth, you can add `intel_idle.max_cstate=10`. This parameter is specific to the `intel_idle` driver and has no effect on AMD systems. In practice, the driver already defaults to allowing all supported C-states, so this is rarely needed — but it does no harm on Intel.

Apply the changes:

```bash
sudo update-grub
```

### A note on NVMe power states

You may see guides recommending `nvme_core.default_ps_max_latency_us=5500` to "enable deep NVMe sleep." This is misleading. That parameter sets a **ceiling** — power states with exit latency above the value are **excluded**. The kernel default is `100000` (100 ms), which already permits the deepest states on virtually all drives. Setting `5500` actually *restricts* your drive from entering its deepest idle states (typically PS4, which has exit latencies around 15 ms on many drives).

If your NVMe is behaving correctly, leave the default alone. If you suspect APST-related issues (drive disappearing after idle, system hangs on wake), the diagnostic step is:

```bash
# Check your drive's power state table
sudo nvme id-ctrl /dev/nvme0 -H | grep -A 3 "PS:"

# Check current APST configuration
sudo nvme get-feature /dev/nvme0 -f 0x0c -H

# Verify the kernel's current setting
cat /sys/module/nvme_core/parameters/default_ps_max_latency_us
```

---

## Step 3: Configure Systemd Sleep and Lid Behavior

Define how long the system should stay in S3 sleep before transitioning to hibernation.

Edit the sleep configuration:

```bash
sudo nano /etc/systemd/sleep.conf
```

Add or uncomment the following lines:

```ini
[Sleep]
AllowSuspendThenHibernate=yes
HibernateMode=platform shutdown
HibernateDelaySec=120min
```

> **Important:** You must include a time unit (`min`, `h`, `s`). If you write `HibernateDelaySec=120` without a unit, systemd interprets it as 120 *seconds* — your laptop will hibernate almost immediately instead of sleeping for two hours.

Next, tell systemd what to do when the lid closes:

```bash
sudo nano /etc/systemd/logind.conf
```

Uncomment and set:

```ini
HandleLidSwitch=suspend-then-hibernate
HandleLidSwitchExternalPower=suspend-then-hibernate
```

---

## Step 4: Bypassing KDE PowerDevil

This is the step most guides miss. KDE Plasma's PowerDevil daemon intercepts lid-close events *before* systemd's `logind` sees them. This creates a conflict:

- If KDE is set to **Sleep**, it calls `systemd-suspend.service` directly, bypassing your `logind.conf` suspend-then-hibernate setting entirely.
- If KDE is set to **Do Nothing**, it places an inhibitor lock that prevents the system from sleeping at all.

There is no KDE GUI option for "Suspend then Hibernate." The solution is to leave KDE set to "Sleep" but redirect what the underlying systemd service actually does.

### Configure KDE

Open **System Settings → Power Management**. Set "When laptop lid closed" to **Sleep** for both AC and Battery profiles.

### Create a systemd drop-in override

Rather than symlinking the service file (which a systemd package update can silently break), we create a drop-in override that survives updates:

```bash
sudo mkdir -p /etc/systemd/system/systemd-suspend.service.d

cat << 'EOF' | sudo tee /etc/systemd/system/systemd-suspend.service.d/override.conf
[Service]
ExecStart=
ExecStart=/usr/lib/systemd/systemd-sleep suspend-then-hibernate
EOF

sudo systemctl daemon-reload
```

The empty `ExecStart=` line is required — systemd accumulates `ExecStart` entries additively, so the blank line clears the original command before setting the replacement. Without it, both commands would run and the unit would fail.

Verify the override is active:

```bash
systemctl cat systemd-suspend.service
```

You should see the original unit file followed by your override under a `# /etc/systemd/system/systemd-suspend.service.d/override.conf` header.

### Why this works

The chain is: **lid close → KDE PowerDevil → "Sleep" → `systemd-suspend.service` → (override) → `suspend-then-hibernate`**. KDE thinks it is triggering a normal suspend, but the drop-in redirects the call. Package updates replace files in `/lib/systemd/system/` but never touch `/etc/systemd/system/`, so the override persists.

---

## The Result

When you close the lid:

1. KDE's PowerDevil fires its "Sleep" action.
2. The overridden `systemd-suspend.service` triggers suspend-then-hibernate.
3. The system enters hardware S3 deep sleep — CPU powers down, RAM stays on, NVMe enters its low-power idle state.
4. An RTC (real-time clock) alarm is set for the configured delay (120 minutes in this example).
5. After the delay, the system briefly wakes, writes the contents of RAM to the swapfile, and powers off completely (true hibernation).
6. On the next power-on, the kernel finds the hibernation image via the `resume` parameters and restores the session.

Battery drain during the S3 phase is minimal (typically < 1% per hour on modern ThinkPads). After hibernation kicks in, drain is zero — the machine is fully powered off.

---

## Troubleshooting

**Hibernation fails silently (system wakes from S3 but doesn't hibernate):**
Check that your swapfile is large enough and that the `resume` and `resume_offset` parameters in GRUB match your current swapfile. If you recreate the swapfile, the offset will change.

```bash
# Verify current offset
sudo filefrag -v /swapfile | awk 'NR==4 {print $4}' | tr -d '.'
```

**System doesn't wake from S3 at all:**
Check `dmesg` after a manual wake for RTC alarm errors. Some BIOS versions have buggy RTC wake implementations — updating the BIOS firmware can help.

**KDE still overrides behavior after update:**
Re-check that PowerDevil is set to "Sleep" (not "Shutdown" or "Do Nothing") and that the drop-in is still in place:

```bash
systemctl cat systemd-suspend.service
```

Photo by <a href="https://unsplash.com/@agforl24?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">Tai Bui</a> on <a href="https://unsplash.com/photos/a-cat-sleeping-on-top-of-a-laptop-computer-wjK7o1j7F-Y?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">Unsplash</a>
      