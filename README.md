# Rex

## Rex is a simple CLI-Interface using asyncio and aioconsole.

Commands are mapped using an nested dictionary containing async functions.
When parsing a command the nested dictionary gets traversed like a tree and the leftover
parts are given as arguments to the found function.

Autocomplete / History / Syntax hints are all automatically generated from the cmd-dictionary
