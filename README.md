[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/DxqGQVx4)


## Working with the database (migrations)

Use the project virtualenv when running Flask / Alembic commands. Activate the venv:

```bash
source .venv/bin/activate
```

When you source the venv, the activate script sets a couple of useful environment variables and helper functions automatically:

- FLASK_APP=run (so `flask` commands will use the `run` module)
- FLASK_ENV=development
- flaskdb_migrate "message" → wrapper for `python -m flask db migrate -m "message"`
- flaskdb_upgrade → wrapper for `python -m flask db upgrade`
- flask_app_run → starts the dev server (`python -m flask run`)

These helpers are available only inside the venv and are automatically removed/restored when you run `deactivate`.

To create and apply a migration after changing `app/models.py`:

```bash
# create migration
flaskdb_migrate "describe your change - your name"

# apply migration
flaskdb_upgrade
```

## Delivered Documents Case 

Information on how to install/use the application barter.com 
[+......]

Link to Kanban Board: 
https://flyer-tray-35034484.figma.site 

Link to Application Structure:
https://punch-guide-99957516.figma.site 

Link to Final User Stories: 

Link to Flowchart [+flowtabllen?]
https://amused-clip-14241862.figma.site 

Link to User Interface prototype:
https://www.figma.com/design/qhGCSW6y5SfgpUuQqfOpyZ/Barter.com---group-23---User-Interface?node-id=5-59&p=f 

Link to audio/video recording of feedback sessions with external partner + Meeting Summaries:

Link to Explanation Algorithm [figma+docu]

