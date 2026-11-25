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
  id INTEGER PRIMARY KEY, orden INTEGER NOT NULL, sa INTEGER,
  ie TEXT NOT NULL DEFAULT '', titulo TEXT NOT NULL DEFAULT ''
);
CREATE TABLE actividad_indicadores (
  actividad INTEGER NOT NULL REFERENCES actividades(id) ON DELETE CASCADE,
  il TEXT NOT NULL, peso REAL, orden INTEGER NOT NULL,
  PRIMARY KEY (actividad, il)
);
CREATE TABLE datos_generales (campo TEXT PRIMARY KEY, valor TEXT NOT NULL DEFAULT '');
CREATE TABLE familias (campo TEXT PRIMARY KEY, valor TEXT NOT NULL DEFAULT '');
CREATE TABLE redaccion (
  clave TEXT PRIMARY KEY, tipo TEXT NOT NULL, valor TEXT NOT NULL DEFAULT ''
);
CREATE TABLE categorias (
  id INTEGER PRIMARY KEY, nombre TEXT NOT NULL DEFAULT '', orden INTEGER NOT NULL
);
CREATE TABLE categoria_opciones (
  id INTEGER PRIMARY KEY, categoria INTEGER NOT NULL REFERENCES categorias(id) ON DELETE CASCADE,
  nombre TEXT NOT NULL, orden INTEGER NOT NULL
);
CREATE TABLE indicador_categoria (
  indicador INTEGER NOT NULL,
  categoria INTEGER NOT NULL REFERENCES categorias(id) ON DELETE CASCADE,
  opcion INTEGER NOT NULL REFERENCES categoria_opciones(id) ON DELETE CASCADE,
  PRIMARY KEY (indicador, categoria)
);
