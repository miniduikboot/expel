@ECHO OFF

REM Start EXPEL in a container and forward arguments to there

SETLOCAL ENABLEEXTENSIONS

REM START WINDOWS-SPECIFIC SECTION
REM from https://steve-jansen.github.io/guides/windows-batch-scripting/part-10-advanced-tricks.html
REM this pauses the terminal after execution when you doubleclick the launcher
SET interactive=0
ECHO %CMDCMDLINE% | FINDSTR /L %COMSPEC% >NUL 2>&1
IF %ERRORLEVEL% == 0 SET interactive=1
REM END WINDOWS-SPECIFIC SECTION

REM if using doubleclick, allow setting the task name via the file name
IF "%interactive%"=="0" (
   SET args="%*"
) ELSE (
   SET args="%~n0"
)

docker run -it --rm ^
    --mount type=bind,src="%CD%",dst=/work ^
    expel-launcher ^
    --windows ^
    --docker-host="tcp://host.docker.internal:2375" ^
    --working-directory="%CD%" ^
    %args%

REM START WINDOWS-SPECIFIC SECTION
REM Contrary the documentation, for doubleclick sessions you need to check with 1 here
IF "%interactive%"=="1" PAUSE
EXIT /B 0
REM END WINDOWS-SPECIFIC SECTION
