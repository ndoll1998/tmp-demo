import { Routes } from '@angular/router';
import { ChatPageComponent } from './chat-page/chat-page.component';

export const routes: Routes = [{ path: '', component: ChatPageComponent }, { path: 'chatPage', component: ChatPageComponent }];