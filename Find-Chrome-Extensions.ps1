$extensions = @()
$users = @()
$chrome = @( 'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe' )
$chrome_extensions_path = @( 'AppData\Local\Google\Chrome\User Data\Default\Extensions' )


function Get-Chrome-Extension-Manifest
{
    Param([string]$extension_path)

    ForEach ( $file in Get-ChildItem -Recurse $extension_path ) {
        if ( $file.name -eq 'manifest.json' ) {
            $object = (Get-Content $file.FullName | Out-String | ConvertFrom-Json)
            $name = $object.name
            If ( $name.StartsWith("_") ) {
                $root = $(Split-Path -Path $file.FullName)
                $local_paths = @( "$root\_locales\en_US\messages.json",
                                 "$root\_locales\en\messages.json"
                )
                ForEach ( $messages in $local_paths ) {
                    if ( Test-Path  $messages ){
                        $message_object = (Get-Content $messages | Out-String | ConvertFrom-Json)
                        if (-Not( $message_object.appName.message -eq $null )) {
                            $name = $message_object.appName.message
                        }
                        if (-Not( $message_object.extName.message -eq $null )) {
                            $name = $message_object.extName.message
                        }
                        if (-Not( $message_object.app_name.message -eq $null )) {
                            $name = $message_object.app_name.message
                        }
                        
                    }
                }
            }
            $version = $object.version
            $User = $extension_path.Split("\")[2]
            $Id = $extension_path.Split("\")[-1]
            $extension = New-Object PSObject -Prop (@{'Name' = $name;
                                                      'Version' = $version;
                                                      'Id' = $id;
                                                      'User' = $User })
            return $extension
        }
    }
}
if (-Not $(Test-Path $chrome)) {
    Write-Error "No Chrome exists"
}

$USERS_PATH="$env:HOMEDRIVE\Users\"
ForEach ( $USER in Get-ChildItem -Path $USERS_PATH ) {
    $users += "$($USERS_PATH)$($USER.Name)"
}

ForEach ( $USER in $users ) {
    if ( Test-Path $USER\$chrome_extensions_path ) {
        ForEach ( $extension_path in Get-ChildItem $USER\$chrome_extensions_path ) {
            $extension = Get-Chrome-Extension-Manifest $extension_path.FullName
            $extensions += $extension
        }
    }
}

$extensions | Format-Table