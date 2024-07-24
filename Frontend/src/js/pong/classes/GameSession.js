// GameSession.js
import socket from '../socket.js';
import { initializeEventHandlers } from '../eventhandlers.js';
import { translateCoordinates } from '../utils.js';
import Paddle from './Paddle.js';
import Ball from './Ball.js';
import PlayingField from './PlayingField.js';
import { LEFT_PADDLE_START, RIGHT_PADDLE_START } from '../constants.js';

class GameSession {
    constructor() {
        this.gameId = null;
        this.localPlayer1Id = null;
        this.localPlayer2Id = null;
        this.isRemote = false; // Flag to distinguish between remote and local multiplayer
        this.socket = socket;  // Attach the socket instance
        this.playingField = null;
        this.leftPaddle = null;
        this.rightPaddle = null;
        this.ball = null;
    }

    initialize(gameId, player1Id, player2Id, isRemote, scene) {
        this.gameId = gameId;
        this.localPlayer1Id = player1Id;
        this.localPlayer2Id = player2Id;
        this.isRemote = isRemote;

        this.playingField = new PlayingField(scene);
        this.leftPaddle = new Paddle(scene, LEFT_PADDLE_START, 0x00ff00);
        this.rightPaddle = new Paddle(scene, RIGHT_PADDLE_START, 0xff0000);
        this.ball = new Ball(scene);
    
        this.playingField.addToScene();
        this.leftPaddle.addToScene();
        this.rightPaddle.addToScene();
        this.ball.addToScene();

        // Always connect to the server
        if (!this.socket.connected) {
            this.socket.connect();
           
            console.log("jooh")
        }
        initializeEventHandlers(this);

        console.log(`Game Session Initialized: gameId=${gameId}, player1Id=${player1Id}, player2Id=${player2Id}, remote=${isRemote}`);
    }

    sendMovement(data) {
        this.socket.emit('move_paddle', data);
    }

    handleGameStateUpdate(data) {
        const translatedData = translateCoordinates(data);
        this.leftPaddle.updatePosition(translatedData.player1_position);
        this.rightPaddle.updatePosition(translatedData.player2_position);
        this.ball.updatePosition(translatedData.ball);
    }

    disconnect() {
        if (this.socket.connected) {
            this.socket.disconnect();
            console.log('Disconnected from server');
        }
    }
}

export default GameSession;
