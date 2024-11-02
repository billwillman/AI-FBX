@echo off
echo CurrentDir: %~dp0
cd %~dp0
Python PyFBXCombine.py gen-npy "./example_json" "hero_kof_kyo_body_0002"
pause