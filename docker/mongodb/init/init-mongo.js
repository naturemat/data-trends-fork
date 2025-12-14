#!/bin/bash
# Script de inicialización para MongoDB
# Se ejecuta automáticamente al crear el contenedor

echo "Inicializando base de datos scraper_db..."

# Esperar a que MongoDB esté listo
sleep 10

# Crear colección trends con validación de esquema
mongosh --host localhost -u admin -p password123 --authenticationDatabase admin scraper_db <<EOF

// Crear colección trends con esquema de validación
db.createCollection("trends", {
  validator: {
    \$jsonSchema: {
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
          description: "Texto de la tendencia/hashtag"
        },
        numeroDeTwits: {
          bsonType: ["int", "null"],
          description: "Número de tweets (puede ser null)"
        },
        pais: {
          bsonType: "string",
          description: "País de origen de la tendencia"
        },
        scraped_at: {
          bsonType: "date",
          description: "Fecha y hora del scraping"
        }
      }
    }
  }
});

// Crear índices para optimizar consultas
db.trends.createIndex({ "fecha": 1, "hora": 1 });
db.trends.createIndex({ "pais": 1 });
db.trends.createIndex({ "tendencia": 1 });
db.trends.createIndex({ "scraped_at": -1 });
db.trends.createIndex({ "pais": 1, "fecha": -1 });

// Insertar documento de ejemplo
db.trends.insertOne({
  "fecha": "2025-12-12",
  "hora": "20:30:00",
  "tendencia": "#Ejemplo",
  "numeroDeTwits": 1000,
  "pais": "worldwide",
  "scraped_at": new Date()
});

print("Base de datos inicializada correctamente");
print("Colecciones creadas:");
db.getCollectionNames().forEach(function(collection) {
  print(" - " + collection);
});

EOF

echo "Inicialización completada."