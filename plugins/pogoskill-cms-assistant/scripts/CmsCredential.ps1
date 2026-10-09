$script:CmsCredentialTarget = 'PoGoskillCMS/OpenAPI'

if (-not (Get-Variable -Name CmsCredentialFallbackRoot -Scope Script -ErrorAction SilentlyContinue)) {
  $localAppData = [Environment]::GetFolderPath([Environment+SpecialFolder]::LocalApplicationData)
  if ([string]::IsNullOrWhiteSpace($localAppData)) {
    throw 'LOCALAPPDATA is unavailable; CMS credential storage cannot be initialized.'
  }
  $script:CmsCredentialFallbackRoot = Join-Path $localAppData 'PoGoskillCMS'
}
$script:CmsCredentialFallbackPath = Join-Path $script:CmsCredentialFallbackRoot 'OpenAPI.v1.dat'
$script:CmsCredentialEntropy = [Text.Encoding]::UTF8.GetBytes('PoGoskillCMS/OpenAPI/v1')

if (-not ('CmsCredentialNative' -as [type])) {
  Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;

public static class CmsCredentialNative
{
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct Credential
    {
        public uint Flags;
        public uint Type;
        public string TargetName;
        public string Comment;
        public System.Runtime.InteropServices.ComTypes.FILETIME LastWritten;
        public uint CredentialBlobSize;
        public IntPtr CredentialBlob;
        public uint Persist;
        public uint AttributeCount;
        public IntPtr Attributes;
        public string TargetAlias;
        public string UserName;
    }

    [DllImport("advapi32.dll", EntryPoint = "CredWriteW", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern bool CredWrite(ref Credential credential, uint flags);

    [DllImport("advapi32.dll", EntryPoint = "CredReadW", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern bool CredRead(string target, uint type, uint flags, out IntPtr credentialPtr);

    [DllImport("advapi32.dll", SetLastError = false)]
    private static extern void CredFree(IntPtr buffer);

    public static void Write(string target, string userName, string secret)
    {
        IntPtr blob = Marshal.StringToCoTaskMemUni(secret);
        try
        {
            Credential credential = new Credential();
            credential.Type = 1;
            credential.TargetName = target;
            credential.CredentialBlobSize = (uint)(secret.Length * 2);
            credential.CredentialBlob = blob;
            credential.Persist = 2;
            credential.UserName = userName;
            if (!CredWrite(ref credential, 0))
                throw new Win32Exception(Marshal.GetLastWin32Error());
        }
        finally
        {
            Marshal.ZeroFreeCoTaskMemUnicode(blob);
        }
    }

    public static string Read(string target)
    {
        IntPtr credentialPtr;
        if (!CredRead(target, 1, 0, out credentialPtr))
        {
            int error = Marshal.GetLastWin32Error();
            if (error == 1168) return null;
            throw new Win32Exception(error);
        }

        try
        {
            Credential credential = (Credential)Marshal.PtrToStructure(credentialPtr, typeof(Credential));
            if (credential.CredentialBlob == IntPtr.Zero || credential.CredentialBlobSize == 0)
                return String.Empty;
            return Marshal.PtrToStringUni(credential.CredentialBlob, (int)credential.CredentialBlobSize / 2);
        }
        finally
        {
            CredFree(credentialPtr);
        }
    }
}
'@
}

function Set-CmsUserOnlyAcl {
  param(
    [Parameter(Mandatory = $true)][string]$LiteralPath,
    [switch]$Container
  )

  $identity = [Security.Principal.WindowsIdentity]::GetCurrent().User
  if ($null -eq $identity) { throw 'Current Windows user SID is unavailable.' }

  if ($Container) {
    $security = [Security.AccessControl.DirectorySecurity]::new()
    $rule = [Security.AccessControl.FileSystemAccessRule]::new(
      $identity,
      [Security.AccessControl.FileSystemRights]::FullControl,
      [Security.AccessControl.InheritanceFlags]'ContainerInherit, ObjectInherit',
      [Security.AccessControl.PropagationFlags]::None,
      [Security.AccessControl.AccessControlType]::Allow
    )
  }
  else {
    $security = [Security.AccessControl.FileSecurity]::new()
    $rule = [Security.AccessControl.FileSystemAccessRule]::new(
      $identity,
      [Security.AccessControl.FileSystemRights]::FullControl,
      [Security.AccessControl.AccessControlType]::Allow
    )
  }

  $security.SetOwner($identity)
  $security.SetAccessRuleProtection($true, $false)
  [void]$security.AddAccessRule($rule)
  Set-Acl -LiteralPath $LiteralPath -AclObject $security -ErrorAction Stop
}

function Set-CmsFallbackApiKey {
  param([Parameter(Mandatory = $true)][string]$ApiKey)

  if (-not (Test-Path -LiteralPath $script:CmsCredentialFallbackRoot -PathType Container)) {
    [void](New-Item -ItemType Directory -Path $script:CmsCredentialFallbackRoot -Force)
  }
  Set-CmsUserOnlyAcl -LiteralPath $script:CmsCredentialFallbackRoot -Container

  $plainBytes = [Text.Encoding]::UTF8.GetBytes($ApiKey)
  $protectedBytes = $null
  try {
    $protectedBytes = [Security.Cryptography.ProtectedData]::Protect(
      $plainBytes,
      $script:CmsCredentialEntropy,
      [Security.Cryptography.DataProtectionScope]::LocalMachine
    )
    $payload = [Convert]::ToBase64String($protectedBytes)
    [IO.File]::WriteAllText(
      $script:CmsCredentialFallbackPath,
      $payload,
      [Text.UTF8Encoding]::new($false)
    )
    Set-CmsUserOnlyAcl -LiteralPath $script:CmsCredentialFallbackPath
  }
  catch {
    if (Test-Path -LiteralPath $script:CmsCredentialFallbackPath -PathType Leaf) {
      Remove-Item -LiteralPath $script:CmsCredentialFallbackPath -Force -ErrorAction SilentlyContinue
    }
    throw
  }
  finally {
    if ($null -ne $plainBytes) { [Array]::Clear($plainBytes, 0, $plainBytes.Length) }
    if ($null -ne $protectedBytes) { [Array]::Clear($protectedBytes, 0, $protectedBytes.Length) }
    $payload = $null
  }
}

function Get-CmsFallbackApiKey {
  if (-not (Test-Path -LiteralPath $script:CmsCredentialFallbackPath -PathType Leaf)) {
    return $null
  }

  $protectedBytes = $null
  $plainBytes = $null
  try {
    $payload = [IO.File]::ReadAllText($script:CmsCredentialFallbackPath, [Text.Encoding]::UTF8).Trim()
    $protectedBytes = [Convert]::FromBase64String($payload)
    $plainBytes = [Security.Cryptography.ProtectedData]::Unprotect(
      $protectedBytes,
      $script:CmsCredentialEntropy,
      [Security.Cryptography.DataProtectionScope]::LocalMachine
    )
    $apiKey = [Text.Encoding]::UTF8.GetString($plainBytes).Trim()
    if ($apiKey -notmatch '^AFS[0-9A-Za-z-]+$') {
      throw 'Local CMS credential file is invalid.'
    }
    return $apiKey
  }
  finally {
    if ($null -ne $plainBytes) { [Array]::Clear($plainBytes, 0, $plainBytes.Length) }
    if ($null -ne $protectedBytes) { [Array]::Clear($protectedBytes, 0, $protectedBytes.Length) }
    $payload = $null
    $apiKey = $null
  }
}

function Get-CmsNativeErrorCode {
  param([Parameter(Mandatory = $true)]$ErrorRecord)
  $current = $ErrorRecord.Exception
  while ($null -ne $current) {
    if ($current -is [ComponentModel.Win32Exception]) {
      return $current.NativeErrorCode
    }
    $current = $current.InnerException
  }
  return $null
}

function Set-CmsStoredApiKey {
  param(
    [Parameter(Mandatory = $true)][string]$ApiKey,
    [switch]$SkipCredentialManager
  )
  if ([string]::IsNullOrWhiteSpace($ApiKey) -or $ApiKey.Trim().Length -lt 20) {
    throw 'CMS API key appears incomplete; credential was not saved.'
  }
  if ($ApiKey.Trim() -notmatch '^AFS[0-9A-Za-z-]+$') {
    throw 'Clipboard does not contain a valid CMS API key; credential was not saved.'
  }

  $normalizedKey = $ApiKey.Trim()
  Set-CmsFallbackApiKey -ApiKey $normalizedKey

  $nativeSaved = $false
  $nativeErrorCode = $null
  if (-not $SkipCredentialManager) {
    try {
      [CmsCredentialNative]::Write($script:CmsCredentialTarget, 'X-API-KEY', $normalizedKey)
      $nativeSaved = $true
    }
    catch {
      $nativeErrorCode = Get-CmsNativeErrorCode -ErrorRecord $_
    }
  }
  $normalizedKey = $null

  return [PSCustomObject]@{
    FallbackSaved = $true
    CredentialManagerSaved = $nativeSaved
    CredentialManagerErrorCode = $nativeErrorCode
    FallbackPath = $script:CmsCredentialFallbackPath
  }
}

function Get-CmsStoredApiKey {
  param([switch]$SkipCredentialManager)

  $fallbackError = $null
  try {
    $fallbackKey = Get-CmsFallbackApiKey
    if (-not [string]::IsNullOrWhiteSpace($fallbackKey)) { return $fallbackKey }
  }
  catch {
    $fallbackError = $_
  }

  if (-not $SkipCredentialManager) {
    try {
      $nativeKey = [CmsCredentialNative]::Read($script:CmsCredentialTarget)
      if (-not [string]::IsNullOrWhiteSpace($nativeKey)) {
        try { Set-CmsFallbackApiKey -ApiKey $nativeKey } catch { }
        return $nativeKey
      }
    }
    catch {
      $nativeErrorCode = Get-CmsNativeErrorCode -ErrorRecord $_
      if ($null -eq $fallbackError -and $nativeErrorCode -ne 1312) { throw }
    }
  }

  if ($null -ne $fallbackError) {
    throw 'Stored CMS credential exists but the protected local copy could not be read.'
  }
  return $null
}
