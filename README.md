# Election Voting System

An online election voting platform built with Flask and MongoDB. This application allows registered voters to vote securely in different election events. Each voter can only vote once per election, and the system prevents multiple submissions from the same user.

## Features

- **Login system** for registered voters.
- **Election selection**: Users can select from available election events.
- **Candidate selection**: After choosing an election, users can view and vote for candidates.
- **Vote tracking**: Each vote is recorded securely with a timestamp.
- **Single vote per user**: Voters can only vote once per election to prevent multiple submissions.
- **MongoDB**: The application uses MongoDB for storing election and vote data.

## Technologies Used

- **Flask**: Web framework for building the app.
- **MongoDB**: NoSQL database for storing election and vote data.
- **HTML/CSS**: For frontend structure and styling.
- **JavaScript**: For dynamic behavior (like loading candidates based on selected election).
- **Jinja2**: Templating engine for rendering dynamic content in HTML templates.

## Setup Instructions

1. Clone this repository to your local machine:
   ```bash
   git clone https://github.com/abdiwasac21/voting_system.git
   cd voting_system
