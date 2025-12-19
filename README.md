[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/DxqGQVx4)


## Database Design

The Entity-Relationship Diagram (ERD) represents the conceptual data model of the application and is provided in `erd.md`.

The physical database schema is implemented in PostgreSQL and defined using Data Definition Language (DDL). The complete DDL used in Supabase can be found in `schema.sql`.


## Delivered Documents Case 

# Information on how to install/use the application barter.com 
[Use the project virtualenv when running Flask / Alembic commands. Activate the venv:

```bash
source .venv/bin/activate
pip install -r requirements.txt
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
#create migration
flaskdb_migrate "describe your change - your name"

#apply migration
flaskdb_upgrade]




#Link to Kanban Board: 
- https://flyer-tray-35034484.figma.site 

# Link to Application Structure:
- https://punch-guide-99957516.figma.site 

# Link to Final User Stories: 
- https://github.com/A-D-DBS-application/web-application-2025-group-23/blob/e2584391a1ed51dff4c00ca68ce5ef0112319973/barter.com%20-%20group%2023%20-%20final%20UserStories.pdf

# Link to Flowchart
- https://amused-clip-14241862.figma.site
- https://github.com/A-D-DBS-application/web-application-2025-group-23/blob/b3642c580e0d294ec81d414be1436f7c8dd8caa6/barter.com%20-%20group23%20-%20final%20flow.pdf

# Link to User Interface prototype:
- https://www.figma.com/design/qhGCSW6y5SfgpUuQqfOpyZ/Barter.com---group-23---User-Interface?node-id=5-59&t=VP867ypVz8lcFcYZ-1

# Link to audio/video recording of feedback sessions with external partner + Meeting Summaries [+presentatiesGebruiktTijdensCall?]:

# Link to Explanation Algorithm [figma+docu]

