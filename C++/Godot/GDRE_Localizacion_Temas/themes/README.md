# themes/

- El tema oscuro es el upstream: `standalone/gdre_theme.tres`.
- El tema claro **no se versiona a mano**: se genera con `generar_tema_claro.py`
  (mapeo explícito de fondos). Así sobrevive a actualizaciones del tema base.
- El conmutador claro/oscuro vive en `gdre_main.gd` (pendiente): alternar el
  `theme` aplicado + persistir en `user://gdre_settings.cfg`.
