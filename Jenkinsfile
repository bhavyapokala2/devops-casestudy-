pipeline {
    agent any
    stages {
        stage('Build Docker Image') {
            steps {
                echo "Build Docker Image"
                bat "docker build -t kubdemoapp:v1 ."
            }
        }
        stage('Docker Login') {
            steps {
                bat 'docker login -u bhavyasrip -p Bhavya2612@@'
            }
        }
        stage('Push Docker Image to Docker Hub') {
            steps {
                echo "push Docker Image to Docker Hub"
                bat "docker tag bhavyasrip/url-shortener:latest bhavyasrip/url-shortener:latest"
                bat "docker push bhavyasrip/url-shortener:latest"
            }
        }
        stage('Deploy to Kubernetes') {
            steps {
                bat 'kubectl apply -f k8s-deployment.yaml --validate=false'
                bat 'kubectl apply -f k8s-service.yaml'
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
    }
}