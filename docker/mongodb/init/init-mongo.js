// Script de inicializacion de MongoDB para la base scraper_db.
//
// Este archivo se monta en /docker-entrypoint-initdb.d (ver docker-compose.yml).
// La imagen oficial de mongo lo ejecuta UNA sola vez, al crear el contenedor
// vacio, con: mongosh <MONGO_INITDB_DATABASE> <este archivo>.
//
// Eso significa que:
//   - la base de datos ya viene seleccionada, no hay que conectarse a mano
//   - la autenticacion la resuelve el entrypoint con las credenciales del
//     contenedor, asi que este archivo NO debe contener usuario ni contrasena
//   - cuando el volumen ya tiene datos, este script no se vuelve a ejecutar

print("Inicializando la base de datos " + db.getName() + "...");

// Coleccion de tendencias con validacion de esquema.
// Asi se rechaza cualquier documento incompleto en lugar de guardarlo en silencio.
db.createCollection("trends", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["fecha", "hora", "tendencia", "numeroDeTwits", "pais", "scraped_at"],
      properties: {
        fecha: {
          bsonType: "string",
          description: "Fecha en formato YYYY-MM-DD"
        },
        hora: {
          bsonType: "string",
          description: "Hora en formato HH:MM:SS"
        },
        tendencia: {
          bsonType: "string",
          description: "Texto de la tendencia o hashtag"
        },
        numeroDeTwits: {
          bsonType: ["int", "null"],
          description: "Numero de tweets, puede ser null"
        },
        pais: {
          bsonType: "string",
          description: "Pais de origen de la tendencia"
        },
        scraped_at: {
          bsonType: "date",
          description: "Fecha y hora del scraping"
        }
      }
    }
  }
});

// Indices que soportan las agregaciones de app/models.py
db.trends.createIndex({ "fecha": 1, "hora": 1 });
db.trends.createIndex({ "pais": 1 });
db.trends.createIndex({ "tendencia": 1 });
db.trends.createIndex({ "scraped_at": -1 });
db.trends.createIndex({ "pais": 1, "scraped_at": -1 });

// Documento de ejemplo, util para levantar el entorno sin scrapear primero
db.trends.insertOne({
  "fecha": "2025-12-12",
  "hora": "20:30:00",
  "tendencia": "#Ejemplo",
  "numeroDeTwits": 1000,
  "pais": "worldwide",
  "scraped_at": new Date()
});

print("Base de datos inicializada. Colecciones: " + db.getCollectionNames().join(", "));
