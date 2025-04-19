@echo off
REM Clean up generated PDF, Markdown, and PNG files in the current directory
del /Q "*_pdfmd.pdf"
del /Q "*_pdfcrop.pdf"
REM Delete markdown files except README.md
FOR %%F IN (*.md) DO (
    IF /I NOT "%%~nxF"=="README.md" DEL /Q "%%F"
)
del /Q "*.png"
echo Cleanup complete.