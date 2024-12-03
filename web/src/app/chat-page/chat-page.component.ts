import { Component, OnDestroy, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ChatService } from '../services/chat.service';
import { Subscription } from 'rxjs';
import { NgFor, NgIf } from '@angular/common';

@Component({
  selector: 'app-chat-page',
  standalone: true,
  imports: [
    FormsModule, NgFor, NgIf
  ],
  templateUrl: './chat-page.component.html',
  styleUrl: './chat-page.component.scss'
})

export class ChatPageComponent implements OnInit, OnDestroy {
  private messagesSubscription!: Subscription;
  messages: any[] = [];
  newMessage: string = '';

  constructor(private chatService: ChatService) { }

  sendMessage() {
    this.messagesSubscription = this.chatService.getMessages().subscribe(
      (message) => {
        message.type = 'text';
        if (message.role === 'assistant') {
          if (message.additional_kwargs) {
            for (const prop in message.additional_kwargs['tool_calls']) {
              let property = message.additional_kwargs['tool_calls'][prop];
              if (property['function']['name'] == 'python') {
                let args = JSON.parse((property['function']['arguments']));
                let lines = args.code.split(/\r?\n|\r|\n/g);
                for (let line of lines) {
                  line.replace('null','');
                  message.content += '' + line + '<br/>';
                }
                message.type = 'code';
              }
            }
          }
        }
        if (message.role === 'system') {
          return;
        }
        this.messages.push(message);
      },
      (err) => console.error(err),
      () => console.log('WebSocket connection closed')
    );
    this.chatService.sendMessage(this.newMessage);
    this.newMessage = '';
  }

  ngOnDestroy() {
    this.messagesSubscription.unsubscribe();
    this.chatService.close();
  }

  ngOnInit(): void {
    //this.chatService.reset();
  }
}
