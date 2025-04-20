@echo off
REM Clean up generated PDF, Markdown, and PNG files in the current directory
del /Q "*_pdfmd.md"
del /Q "*_pdfcrop_*.pdf"
del /Q "*_pdfsplit_*.pdf"
del /Q "*_excelpdf_*.pdf"
REM Delete markdown files except README.md
FOR %%F IN (*.md) DO (
    IF /I NOT "%%~nxF"=="README.md" DEL /Q "%%F"
)
del /Q "*.png"
echo Cleanup complete.