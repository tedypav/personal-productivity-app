$a = (New-Object -COM WScript.Shell).CreateShortcut("$env:USERPROFILE\Desktop\Productivity App.lnk")
$a.TargetPath = "C:\Users\Asus\AppData\Local\Programs\Python\Python313\python.exe"
$a.Arguments = """C:\Users\Asus\Desktop\Personal\Professional Development\SoftUni Courses\AI Assisted Development\personal-productivity-app\run.py"""
$a.IconLocation = "C:\Users\Asus\Desktop\Personal\Professional Development\SoftUni Courses\AI Assisted Development\personal-productivity-app\assets\icons\logo_icon.ico,0"
$a.WorkingDirectory = "C:\Users\Asus\Desktop\Personal\Professional Development\SoftUni Courses\AI Assisted Development\personal-productivity-app"
$a.Save()
Write-Host "Shortcut created on Desktop"
