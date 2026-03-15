# Repository Notes

- In this repository, before running PowerShell commands that print file contents or search results, set console output encoding to UTF-8 first:
  `$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()`
- Prefer `Get-Content -Encoding UTF8` when reading source files that may contain Chinese text.
- After analyzing or comparing local video files, delete any temporary artifacts you created before finishing unless the user explicitly asks to keep them. This includes extracted frames, ffmpeg outputs, scratch images, and `_tmp*` files or directories.
