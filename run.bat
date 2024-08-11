@echo off
REM Load environment variables from .env file
for /f "tokens=1,2 delims==" %%A in (.env) do set %%A=%%B

set PGPASSWORD=%DB_PASSWORD%

echo Running create_tables.sql...
psql -h %DB_HOST% -U %DB_USER% -d %DB_NAME% -f create_tables.sql

if %errorlevel% neq 0 (
    echo Error running create_tables.sql, aborting.
    exit /b %errorlevel%
) else (
    echo Tables created successfully.
)

echo Running populate_tables.sql...
psql -h %DB_HOST% -U %DB_USER% -d %DB_NAME% -f populate_tables.sql

if %errorlevel% neq 0 (
    echo Error running populate_tables.sql, aborting.
    exit /b %errorlevel%
) else (
    echo Tables populated successfully.
)

echo Running game.py
python game.py

if %errorlevel% neq 0 (
    echo Error running game.py, aborting.
    exit /b/ %errorlevel%
) else (
    echo Script Executed Successfully
)

set PGPASSWORD=

pause
