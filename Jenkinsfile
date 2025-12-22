pipeline {
    agent any

    environment {
        // Le damos a Jenkins la variable para que los tests pasen
        // OJO: En un trabajo real, esto se hace con "credentials", pero para tu Rol 4 esto sirve.
        MONGODB_URL = 'mongodb://Grupo1:passGrupo1@3.151.181.99:27017/scraper_db?authSource=admin'
    }

    stages {
        stage('Preparar Entorno') {
            steps {
                echo '--- Instalando dependencias ---'
                // Instala las librerías necesarias
                sh 'pip install -r requirements.txt'
                sh 'pip install pytest' 
            }
        }

        stage('QA - Tests Automáticos') {
            steps {
                echo '--- Ejecutando Pruebas de Calidad ---'
                // Ejecuta los tests que acabamos de crear
                // Si esto falla, Jenkins marcará el Build como ROJO
                sh 'pytest tests/ --verbose'
            }
        }
        
        // Aquí podrías agregar una etapa de "Deploy" si los tests pasan
        stage('Deploy (Simulado)') {
             steps {
                 echo '--- Tests pasaron: Listo para despliegue ---'
             }
        }
    }
}
