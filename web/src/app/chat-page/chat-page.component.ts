import { Component, OnDestroy, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ChatService } from '../services/chat.service';
import { Subscription } from 'rxjs';
import { NgFor, NgIf } from '@angular/common';
import showdown from 'showdown';
import hljs from 'highlight.js/lib/core';
import python from 'highlight.js/lib/languages/python';

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

  constructor(private chatService: ChatService) {
    hljs.registerLanguage('python', python);
  }

  sendMessage() {
    this.messagesSubscription = this.chatService.getMessages().subscribe(
      (message) => {
        message.type = 'text';
        if (message.role === 'assistant') {
          if (message.additional_kwargs) {
            for (const prop in message.additional_kwargs['tool_calls']) {
              let property = message.additional_kwargs['tool_calls'][prop];
              if (property['function']['name'] == 'python') {
                let pythonCode = JSON.parse((property['function']['arguments']));
                let lines = pythonCode.code.split(/\r?\n|\r|\n/g);
                message.content = '<code>';
                for (let line of lines) {
                  const indentLine = (line: string, count: number) => line.replace(/\t/g, ' '.repeat(count));
                  //indentLine(line, 2);
                  message.content += hljs.highlight(
                    line,
                    { language: 'python' }
                  ).value + '<br/>';
                }
                message.content += '</code>'
                message.type = 'code';
              }
            }
          }
        }
        if (message.role === 'system') {
          let converter: showdown.Converter = new showdown.Converter();
          let html = converter.makeHtml(message.content);
          message.content = html;
          message.type = 'info';
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
