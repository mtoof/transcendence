import { io } from 'socket.io-client';

// Use the proxy path for local development
// const socket = io('/game-server/socket.io');
const socket = io('http://localhost:8010');
console.log("derp")

socket.on('connect', () => {
    console.log('Connected to server');
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
});

socket.on('connect_error', (error) => {
    console.error('Connection error:', error);
});

export default socket;
