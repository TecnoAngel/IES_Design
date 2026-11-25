CREATE TABLE meta (clave TEXT PRIMARY KEY, valor TEXT);
CREATE TABLE config (clave TEXT PRIMARY KEY, valor TEXT);
CREATE TABLE situaciones (
  numero INTEGER PRIMARY KEY, ev INTEGER, titulo TEXT NOT NULL DEFAULT '',
  horas REAL, orden INTEGER NOT NULL
);
CREATE TABLE situacion_campos (
  numero INTEGER NOT NULL REFERENCES situaciones(numero) ON DELETE CASCADE,
  campo TEXT NOT NULL, valor TEXT NOT NULL DEFAULT '',
  PRIMARY KEY (numero, campo)
);
CREATE TABLE criterios_peso (ce TEXT PRIMARY KEY, peso REAL NOT NULL DEFAULT 0);
CREATE TABLE indicadores (
  orden INTEGER PRIMARY KEY, ce TEXT NOT NULL, pil REAL,
  descripcion TEXT NOT NULL DEFAULT '', descriptores TEXT NOT NULL DEFAULT '',
  contenidos TEXT NOT NULL DEFAULT '', transversales TEXT NOT NULL DEFAULT '',
  ie TEXT NOT NULL DEFAULT '', cc TEXT NOT NULL DEFAULT '', ae TEXT NOT NULL DEFAULT '',
  sa INTEGER
);
CREATE TABLE actividades (
  orden INTEGER PRIMARY KEY, il TEXT NOT NULL, descripcion TEXT NOT NULL DEFAULT '', peso REAL
);
CREATE TABLE datos_generales (campo TEXT PRIMARY KEY, valor TEXT NOT NULL DEFAULT '');
CREATE TABLE familias (campo TEXT PRIMARY KEY, valor TEXT NOT NULL DEFAULT '');
