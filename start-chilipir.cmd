@echo off
title Start Chilipir
powershell.exe -NoExit -ExecutionPolicy Bypass -Command "Set-Location 'D:\dev\projects\price-watch-ro'; .\scripts\dev\start-local.ps1; Start-Process 'http://localhost:3000'"
