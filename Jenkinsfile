pipeline {
    agent any

    // Aquí cargamos las credenciales guardadas en Jenkins
    environment {
        // Esto lee el "Secret text" que guardaste como MONGODB_URL
        MONGODB_URL = credentials('MONGODB_URL')
    }

    stages {
        stage('Preparar Entorno') {
            steps {
                echo '--- 1. Instalando Dependencias (Test) ---'
                // Nota: Usamos sed para evitar conflictos de versiones si es necesario
                sh "sed -i 's/Flask-CORS==3.1.1/Flask-CORS/' requirements.txt"
                sh "sed -i 's/openai==0.4.6/openai/' requirements.txt"
                
                // Instalamos dependencias en la máquina de Jenkins para poder testear
                sh 'sudo pip3 install --upgrade pyOpenSSL'
                sh 'sudo pip3 install -r requirements.txt'
                sh 'sudo pip3 install pandas pytest mongomock gunicorn'
            }
        }

        stage('QA - Tests Automáticos') {
            steps {
                echo '--- 2. Ejecutando Pruebas de Calidad (Pytest) ---'
                sh 'pytest tests/ --verbose'
            }
        }

        stage('🚀 Despliegue Remoto (CD)') {
            steps {
                script {
                    // DATOS DE CONEXIÓN A LA INSTANCIA A (PRODUCCIÓN)
                    def prodIP = "172.31.39.188"
                    def remoteUser = "ubuntu"
                    def targetDir = "/var/www/scraper/"

                    echo "--- 3. Desplegando a Producción (${prodIP}) ---"

                    // A. Generamos el archivo .env AQUÍ (en Jenkins) usando las credenciales
                    sh """
                        echo "MONGODB_URL=${MONGODB_URL}" > .env
                        echo "FLASK_ENV=production" >> .env
                        echo "API_BASE_URL=http://3.151.181.99:5000" >> .env
                        echo "GROQCLOUD_API_KEY=***REMOVED***" >> .env
                    """

                    // B. Enviamos los archivos a la OTRA máquina usando RSYNC por SSH
                    // Nota: Excluimos cosas innecesarias para que sea rápido
                    sh """
                        rsync -avz -e "ssh -o StrictHostKeyChecking=no" \
                        --exclude='.git' \
                        --exclude='venv' \
                        --exclude='__pycache__' \
                        --exclude='tests' \
                        ./ ${remoteUser}@${prodIP}:${targetDir}
                    """

                    // C. Reiniciamos el servicio en la OTRA máquina
                    sh """
                        ssh -o StrictHostKeyChecking=no ${remoteUser}@${prodIP} \
                        'sudo systemctl restart scraper'
                    """
                }
            }
        }
    }

    post {
        always {
            cleanWs()
            echo '♻️ Workspace limpiado con exito.'
        }
        success {
            echo '🎉 ¡DESPLIEGUE EXITOSO! La Instancia A ha sido actualizada.'
        }
        failure {
            echo '❌ El pipeline falló. Revisa los logs.'
        }
    }
}