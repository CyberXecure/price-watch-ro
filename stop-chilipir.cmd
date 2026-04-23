@echo off
title Stop Chilipir
powershell.exe -NoExit -ExecutionPolicy Bypass -Command "Set-Location 'D:\dev\projects\price-watch-ro'; .\scripts\dev\stop-local.ps1"
