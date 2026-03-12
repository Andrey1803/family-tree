@echo off
chcp 65001 >nul
cd /d "d:\Мои документы\Рабочий стол\hobby\Projects\Family tree"
git status > git_output.txt 2>&1
type git_output.txt
