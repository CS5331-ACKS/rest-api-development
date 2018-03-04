# CS5331 Assignment 1: REST API Development

by [Team CS5331-ACKS](https://github.com/CS5331-ACKS)

Secret Diary is a web application that implements and makes use of the endpoints described in the API specification: https://cs5331-assignments.github.io/rest-api-development/

## Setup

Important files/directories:
- Dockerfile - contains the environment setup scripts to ensure a homogenous development environment
- src/ - contains the front-end code in `html` and the skeleton Flask API code in `service`
- img/ - contains images used for this README

Assuming you're developing on an Ubuntu 16.04 machine, the quick instructions to get up and running are:

### 1. Install Docker

```bash
sudo apt-get update
sudo apt-get install \
    apt-transport-https \
    ca-certificates \
    curl \
    software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"
sudo apt-get update
sudo apt-get install docker-ce
```

(Docker CE installation instructions are from this [link](https://docs.docker.com/install/linux/docker-ce/ubuntu/#install-using-the-repository).)

### 2. Verify Docker Works

```bash
sudo docker run hello-world
```

### 3. Run the app

```bash
sudo ./run.sh
```

### 4. Verify that everything runs correctly

The following ports are expected to be accessible:
- 80, on which static HTML content, including the front-end, is served.
- 8080, on which the API is exposed.

To verify this, run the following commands in a different terminal window:

```bash
curl http://localhost:80
curl http://localhost:8080
```

If a response is received, you're good to go.

## Screenshots

TODO

Please replace the example screenshots with screenshots of your completed project. Feel free to include more than one.

![Sample Screenshot](./img/samplescreenshot.png)

## Administration and Evaluation

### Team Members

1. Andy Tan Guan Ming
2. Zhu Chunqi
3. Lu Yang Kenneth
4. Ng Si Kai

### Short Answer Questions

#### Question 1: Briefly describe the web technology stack used in your implementation.

Back-end tech stack
- Database - Sqlite was used due to its excellent reputation as an embedded database and ease of use.
- Web Framework - Flask, a python web framework was used.

Front-end tech stack
- Bootstrap - For HTML- and CSS-based design template.
- jQuery - JavaScript library to perform AJAX calls and DOM manipulation.

#### Question 2: Are there any security considerations your team thought about?

We have thought about security when implementing the API and web application.
- SSL should be implemented to provide confidentiality, integrity and authentication for network data between client and server.
- Input validation should be implemented to prevent potential injection attacks. e.g. SQL injection, XSS. Command injection and etc.
- Strong user account policy should be implemented. e.g. account lockout, minimum password length, password complexity and etc.
- Access control was implemented. To ensure that authenticated users will not be able to perform horizontal privilege escalation.

#### Question 3: Are there any improvements you would make to the API specification to improve the security of the web application?

TODO

#### Question 4: Are there any additional features you would like to highlight?

TODO

#### Question 5: Is your web application vulnerable? If yes, how and why? If not, what measures did you take to secure it?

The web application is vulnerable.

1. Account lockout mechanism was not implemented. This would result in successful account bruteforce attack, leading to account compromise.
2. Minimum password length not implemented. A short password length would be require less effort and difficulty to compromise.
3. Vulnerable to eavesdropping and man in the middle attack. This would result in sensitive data exposure and potential integrity impact. This is because the network traffic between client and server is unencrypted.
4. Vulnerable to potential DoS attack as rate limiting mechanism is not implemented.
5. Absolute session timeout was not implemented. Session token would still be valid unless the expire endpoint is called. This may increase the probability of an attacker hijacking the session and impersonate the victim.

#### Feedback: Is there any other feedback you would like to give?

Nope :smile:

### Declaration

1. Andy Tan Guan Ming
    - Wrote frontend queries to backend for 'login', 'registration', 'view public diary entries', 'view authenticated diary entries' and 'create diary entry'
2. Zhu Chunqi
    - Designed the database schema for `users` table
    - Implemented the `/users/*` endpoints
3. Lu Yang Kenneth
    - Implemented authentication on each page and design of frontend
    - Organised README and documents for submission
4. Ng Si Kai
    - TODO
