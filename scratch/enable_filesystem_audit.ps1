$ErrorActionPreference = "Stop"

$ProjectPath = "C:\desarrollos\Codex\Easy Date"
$TargetPath = Join-Path $ProjectPath "downloaded_files"
$DocsPath = Join-Path $ProjectPath "docs"
$ReportPath = Join-Path $DocsPath "windows_filesystem_audit_status.txt"
$FileSystemAuditGuid = "{0CCE921D-69AE-11D9-BED3-505054503030}"

New-Item -ItemType Directory -Force -Path $DocsPath | Out-Null
New-Item -ItemType Directory -Force -Path $TargetPath | Out-Null

auditpol /set /subcategory:$FileSystemAuditGuid /success:enable /failure:enable | Out-Null

$sidEveryone = New-Object System.Security.Principal.SecurityIdentifier("S-1-1-0")
$rights = [System.Security.AccessControl.FileSystemRights]"CreateFiles, CreateDirectories, WriteData, AppendData, Delete, DeleteSubdirectoriesAndFiles, WriteAttributes, WriteExtendedAttributes"
$inheritance = [System.Security.AccessControl.InheritanceFlags]"ContainerInherit, ObjectInherit"
$propagation = [System.Security.AccessControl.PropagationFlags]"None"
$auditFlags = [System.Security.AccessControl.AuditFlags]"Success, Failure"
$rule = New-Object System.Security.AccessControl.FileSystemAuditRule($sidEveryone, $rights, $inheritance, $propagation, $auditFlags)

foreach ($path in @($ProjectPath, $TargetPath)) {
    $acl = Get-Acl -LiteralPath $path -Audit
    $acl.SetAuditRule($rule)
    Set-Acl -LiteralPath $path -AclObject $acl
}

$policy = auditpol /get /subcategory:$FileSystemAuditGuid
$projectAudit = (Get-Acl -LiteralPath $ProjectPath -Audit).Audit | Out-String
$targetAudit = (Get-Acl -LiteralPath $TargetPath -Audit).Audit | Out-String

@"
Windows FileSystem Audit Status
Generated: $(Get-Date -Format o)

Policy:
$policy

Project path:
$ProjectPath

Target path:
$TargetPath

Project SACL:
$projectAudit

Downloaded_files SACL:
$targetAudit

Expected event IDs:
- 4663: object access attempt, including write/delete when SACL matches
- 4660: object deleted, if enabled and emitted by policy
- 4656: handle requested, depending on audit policy

Notes:
- This enables auditing from now on. It cannot reconstruct previous create/delete events.
- Security log access may require administrator privileges.
"@ | Set-Content -LiteralPath $ReportPath -Encoding UTF8

Write-Host "OK: Auditoria de File System activada."
Write-Host "Reporte: $ReportPath"
