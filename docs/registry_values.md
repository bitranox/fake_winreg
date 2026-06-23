# Windows Registry Values Reference

This document describes the registry values used in fake_winreg's test registries
and how software detects different Windows versions.

## Detecting Windows Versions

The Windows registry does **not** contain a simple "Windows 11" marker.
Detection relies on build numbers and specific value combinations.

| OS | CurrentBuild | DisplayVersion | ProductName (registry) |
|----|-------------|----------------|------------------------|
| Windows 10 21H2 | 19044 | 21H2 | Windows 10 Pro |
| Windows 10 22H2 | 19045 | 22H2 | Windows 10 Pro |
| Windows 11 21H2 | 22000 | 21H2 | Windows 10 Pro |
| Windows 11 22H2 | 22621 | 22H2 | Windows 10 Pro |
| Windows 11 23H2 | 22631 | 23H2 | Windows 10 Pro |
| Windows 11 24H2 | 26100 | 24H2 | Windows 10 Pro |

**Key rule: `CurrentBuild >= 22000` means Windows 11.**

`ProductName` always reads "Windows 10 ..." even on Windows 11. Microsoft
never updated this value. Software must check `CurrentBuild` or
`DisplayVersion` to distinguish Windows 11 from Windows 10.

## CurrentVersion Key

**Path:** `HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion`

### Version Identification

| Value | Type | Win 10 (18363) | Win 11 23H2 | Notes |
|-------|------|----------------|-------------|-------|
| `CurrentBuild` | REG_SZ | `"18363"` | `"22631"` | Primary version indicator |
| `CurrentBuildNumber` | REG_SZ | `"18363"` | `"22631"` | Same as CurrentBuild |
| `DisplayVersion` | REG_SZ | — | `"23H2"` | Human-readable release name |
| `ProductName` | REG_SZ | `"Windows 10 Pro"` | `"Windows 10 Pro"` | Never updated for Win11 |
| `CurrentVersion` | REG_SZ | `"6.3"` | `"6.3"` | Frozen since Windows 8.1 |
| `CurrentMajorVersionNumber` | REG_DWORD | — | `10` | Frozen at 10 |
| `CurrentMinorVersionNumber` | REG_DWORD | — | `0` | Frozen at 0 |

### Build Metadata

| Value | Type | Win 11 23H2 | Notes |
|-------|------|-------------|-------|
| `UBR` | REG_DWORD | `4317` | Update Build Revision (changes with each cumulative update) |
| `EditionID` | REG_SZ | `"Professional"` | Pro=Professional, Home=Core, Enterprise=Enterprise |
| `InstallationType` | REG_SZ | `"Client"` | Client vs Server |
| `BuildBranch` | REG_SZ | `"ni_release"` | Internal codename (co=21H2, ni=22H2/23H2, ge=24H2) |
| `BuildLab` | REG_SZ | `"22621.ni_release.220506-1250"` | Compile-time tag |
| `BuildLabEx` | REG_SZ | `"22621.1.amd64fre.ni_release.220506-1250"` | Extended compile tag |

**Why BuildLab shows 22621 for 23H2:** Windows 11 23H2 shares the same compiled
OS image as 22H2. The enablement package KB5027397 bumps `CurrentBuild` to 22631
but does not update the compile-time tags (`BuildLab`, `BuildLabEx`).

### Edition Variants

| Edition | ProductName | EditionID |
|---------|------------|-----------|
| Home | Windows 10 Home | Core |
| Pro | Windows 10 Pro | Professional |
| Enterprise | Windows 10 Enterprise | Enterprise |
| Education | Windows 10 Education | Education |
| Pro for Workstations | Windows 10 Pro for Workstations | ProfessionalWorkstation |

### Branch Codenames

| Codename | Branch | Versions |
|----------|--------|----------|
| co | co_release | Windows 11 21H2 |
| ni | ni_release | Windows 11 22H2, 23H2 |
| ge | ge_release | Windows 11 24H2 |

## ProfileList

**Path:** `HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList`

System profiles are identical across Windows 10 and 11:

| SID | Account | ProfileImagePath |
|-----|---------|-----------------|
| S-1-5-18 | Local System | `%systemroot%\system32\config\systemprofile` |
| S-1-5-19 | Local Service | `%systemroot%\ServiceProfiles\LocalService` |
| S-1-5-20 | Network Service | `%systemroot%\ServiceProfiles\NetworkService` |

User profiles use SID format `S-1-5-21-{a}-{b}-{c}-{RID}` where RID starts
at 1000 (first user typically 1001).

## HKEY_USERS

Each user SID from ProfileList appears as a subkey under `HKEY_USERS`.
The `Volatile Environment` subkey contains per-session values like `USERNAME`.

## Wine Detection

Wine registries contain an additional key not present on real Windows:

```
HKEY_LOCAL_MACHINE\Software\Wine
```

The presence of this key is the standard method to detect a Wine environment.
Wine uses its own build numbers (e.g., `CurrentBuild = "7601"` for Wine
emulating Windows 7).

## Test Registries in fake_winreg

fake_winreg ships three pre-built test registries:

| Function | Emulates |
|----------|----------|
| `get_minimal_windows_testregistry()` | Windows 10 (build 18363) |
| `get_minimal_windows11_testregistry()` | Windows 11 23H2 Pro (build 22631) |
| `get_minimal_wine_testregistry()` | Wine environment (build 7601) |

Export all as files:

```bash
fake-winreg export-demo-registries
# Creates: windows10.{json,reg,db}  windows11.{json,reg,db}  wine.{json,reg,db}
```

## Sources

- [Windows 11 release information](https://learn.microsoft.com/en-us/windows/release-health/windows11-release-information)
- [KB5027397 — 23H2 enablement package](https://support.microsoft.com/en-us/topic/kb5027397-feature-update-to-windows-11-version-23h2-by-using-an-enablement-package-b9e76726-3c94-40de-b40b-99decba3db9d)
- [Windows 11 update history (23H2)](https://support.microsoft.com/en-us/topic/windows-11-version-23h2-update-history-59875222-b990-4bd9-932f-91a5954de434)
- [ProductName showing "Windows 10" on Windows 11 — Microsoft Q&A](https://learn.microsoft.com/en-us/answers/questions/711686/win11-machine-is-still-showing-windows-10-as-produ)
