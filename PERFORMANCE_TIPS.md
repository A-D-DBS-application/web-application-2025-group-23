# PERFORMANCE TIPS - Flask App Sneller Maken

## SNELLE OPLOSSINGEN

### 1. Debug Mode Uit = Sneller (maar geen auto-reload)
```bash
# In PowerShell:
$env:FLASK_DEBUG = "false"
python run.py

# Of direct in Windows:
set FLASK_DEBUG=false
python run.py
```

**Voordeel:** ~50% sneller
**Nadeel:** Moet app herstarten bij code wijzigingen

---

### 2. Threaded Mode (al ingebouwd in run.py)
```python
app.run(threaded=True)  # Meerdere requests tegelijk
```

**Voordeel:** Handles multiple requests efficiently
**Nadeel:** Geen extra instellingen nodig

---

### 3. Database Queries Optimaliseren

**SLECHT:**
```python
# Haal ALL users op, dan filter in Python (TRAAG!)
users = User.query.all()
user = [u for u in users if u.id == 123]
```

**GOED:**
```python
# Filter in database (SNEL!)
user = User.query.filter_by(id=123).first()
```

---

### 4. Cache Static Assets
Voeg dit toe aan `app/config.py`:

```python
SEND_FILE_MAX_AGE_DEFAULT = 31536000  # 1 jaar caching
```

Dit helpt de browser files langer in cache te houden.

---

### 5. Lazy Loading van Relationships
```python
# In models.py
class User(db.Model):
    posts = db.relationship('Post', lazy='select')  # Select wanneer nodig
    # lazy='joined' - Load meteen (sneller voor veel queries)
    # lazy='select' - Load on demand (memory-efficient)
```

---

## DIAGNOSTIEK

### Wat is traag?
```bash
# 1. Browser DevTools (F12)
#    → Network tab: zie welke requests traag zijn
#    → Console: zie JS errors

# 2. Flask logging
FLASK_DEBUG=true python run.py
# Toont query times en request info

# 3. Browser cache legen
# Chrome: Ctrl+Shift+Del → "All time" → Clear
```

---

## CHECKLISTE

✅ Debug mode OFF voor testen
✅ Threaded mode ON (standaard nu)
✅ Database queries optimaliseren
✅ Browser cache legen (F12 → Disable cache)
✅ Check network tab voor langzame requests
✅ Controleer CPU/RAM gebruik (Task Manager)

---

## COMMAND REFERENCE

**Snel testen (geen debug):**
```bash
$env:FLASK_DEBUG = "false"
python run.py
```

**Development (debug aan, auto-reload):**
```bash
$env:FLASK_DEBUG = "true"
python run.py
```

**Standaard (leest uit .flaskenv):**
```bash
python run.py
```

---

## TYPICAL SLOW POINTS

1. **Database queries** - Meest waarschijnlijk
   - Zorg dat queries gefilterd zijn in SQL, niet in Python
   
2. **Template rendering** - Bij veel data
   - Paginate grote lijsten
   - Lazy load items

3. **Static files** - Browser cache
   - Clear cache met Ctrl+Shift+Del
   
4. **Network requests** - Externa APIs
   - Async laden indien mogelijk

5. **Debug reloader** - Debug mode aan
   - Zet FLASK_DEBUG=false als je niet debugt

---

## PERFORMANCE MONITORING

Als app nog steeds traag:

### Windows Task Manager
- Ctrl+Shift+Esc
- Python proces zoeken
- CPU en Memory checken

### Flask Debug Mode
```bash
FLASK_DEBUG=true python run.py
# Toont request logs met timing info
```

### Browser DevTools (F12)
- Network tab → zie elke request
- Kijk naar "Time" kolom
- Langste requests = waarschijnlijk database

---

**TL;DR:**
1. Zet `FLASK_DEBUG=false` als je niet aan code werkt
2. Clear browser cache (Ctrl+Shift+Del)
3. Check Network tab in DevTools welke requests traag zijn
4. Threaded mode is al ingeschakeld
