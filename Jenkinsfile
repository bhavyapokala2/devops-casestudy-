
pipeline {
    agent any

    stages {
        stage('Build Docker Image') {
            steps {
                echo "Build Docker Image"
                bat 'docker build -t bhavyasrip/url-shortener:v1 .'
            }
        }

        stage('Run Tests') {
            steps {
                echo "Run Unit Tests"
                bat 'python -m unittest discover -s tests -v'
            }
        }

        stage('Docker Login') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-credentials',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_TOKEN'
                )]) {
                    bat '''
                        echo %DOCKER_TOKEN% | docker login -u %DOCKER_USER% --password-stdin
                    '''
                }
            }
        }

        stage('Push Docker Image to Docker Hub') {
            steps {
                echo "Push Docker Image to Docker Hub"
                bat 'docker push bhavyasrip/url-shortener:v1'
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                echo "Deploy to Kubernetes"

                bat 'kubectl apply -f k8s-deployment.yaml --validate=false'
                bat 'kubectl apply -f k8s-service.yaml'

                bat 'kubectl set image deployment/url-shortener url-shortener=bhavyasrip/url-shortener:v1'
                bat 'kubectl rollout status deployment/url-shortener --timeout=120s'
            }
        }
    }

    post {
        success {
            echo 'Pipeline completed successfully!'
        }

        failure {
            echo 'Pipeline failed. Please check the logs.'
        }

        always {
            bat 'docker logout'
        }
    }
}
