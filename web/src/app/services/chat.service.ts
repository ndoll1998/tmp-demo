import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { WebSocketSubject } from 'rxjs/internal/observable/dom/WebSocketSubject';
import { Observable } from 'rxjs';
import { webSocket } from 'rxjs/webSocket';

@Injectable({
  providedIn: 'root'
})
export class ChatService {

  private socket$: WebSocketSubject<any>;

  constructor(private http: HttpClient) {
    this.socket$ = this.connectWS('ws://localhost:8000/ws/steps');
  }

  connectWS(url: string): WebSocketSubject<any> {
    let ws: WebSocketSubject<any> = webSocket(url);
    let that = this;
    ws.subscribe(
      (message: any) => {
        console.log('Received message:', message);
      },
      (err: any) => console.error(err),
      () => {
        console.log('uuuups');
        that.socket$ = that.connectWS(url);
      }
    );
    return ws;
  }

  sendMessage(msg: any) {
    this.http.post('/api/chat?message="' + msg + '"', '').subscribe(result => {
      console.log('result: ', result);
    });
  }

  getMessages(): Observable<any> {
    return this.socket$.asObservable();
  }

  close() {
    this.socket$.complete();
  }

  reset() {
    this.http.get('http://localhost:8000/reset').subscribe(result => {
      console.log('result: ', result);
    });
  }
}
