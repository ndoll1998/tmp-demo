import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { WebSocketSubject } from 'rxjs/internal/observable/dom/WebSocketSubject';
import { Observable } from 'rxjs';
import { webSocket } from 'rxjs/webSocket';

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private baseWS: string = '/ws/';
  private baseAPI: string = '/api/';
  private socket$!: WebSocketSubject<any>;

  constructor(private http: HttpClient) {
    this.socket$ = this.connectWS();
  }

  connectWS(): WebSocketSubject<any> {
    let ws: WebSocketSubject<any> = webSocket(this.baseWS + 'steps');
    let that = this;
    ws.subscribe(
      (message: any) => {
        console.log('WebSocket received message:', message);
      },
      (err: any) => console.error(err),
      () => {
        console.log('WebSocket disconnected');
        that.socket$ = that.connectWS();
      }
    );
    return ws;
  }

  sendMessage(msg: any) {
    this.http.post(this.baseAPI + 'chat?message="' + msg + '"', '').subscribe(result => {
      console.log('POST /chat result: ', result);
    });
  }

  getMessages(): Observable<any> {
    return this.socket$.asObservable();
  }

  close() {
    this.socket$.complete();
  }

  reset() {
    this.close;
    let that = this;
    this.http.get(this.baseAPI + 'reset').subscribe(result => {
      console.log('POST /reset result: ', result);
      that.socket$ = that.connectWS();
    });
  }
}
