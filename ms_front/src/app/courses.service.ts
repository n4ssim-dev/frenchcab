import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';
import { environment } from '../environments/environment';

// Adresse du gateway (selon l'environnement de build) et mot de passe (GATEWAY_PASSWORD du .env du gateway).
const GATEWAY_URL = environment.gatewayUrl;
const GATEWAY_PASSWORD = '5';

export interface Course {
  id: number;
  vendor_id: number;
  depart: string;
  arrivee: string;
  passagers: number;
  distance: number;
  zone_depart: string | null;
  quartier_depart: string | null;
  zone_arrivee: string | null;
  quartier_arrivee: string | null;
  montant: number;
}

export interface PageCourses {
  total: number;
  limit: number;
  offset: number;
  courses: Course[];
}

interface ReponseGateway {
  success: boolean;
  message: string;
  reponse: PageCourses;
}

export interface DemandePrediction {
  pickup: string;
  id_location_depart: number;
  id_location_arrivee: number;
  distance: number;
}

export interface ResultatPrediction {
  duree_predite_min: number;
}

@Injectable({ providedIn: 'root' })
export class CoursesService {
  private http = inject(HttpClient);

  getCourses(limit: number, offset: number, date: string | null): Observable<PageCourses> {
    let params = new HttpParams().set('limit', limit).set('offset', offset);
    if (date) {
      params = params.set('date', date); // format AAAA-MM-JJ
    }
    return this.http
      .get<ReponseGateway>(`${GATEWAY_URL}/courses`, {
        params,
        headers: { 'x-api-password': GATEWAY_PASSWORD },
      })
      .pipe(map((r) => r.reponse));
  }

  predireDuree(demande: DemandePrediction): Observable<ResultatPrediction> {
    return this.http
      .post<{ reponse: ResultatPrediction }>(`${GATEWAY_URL}/predictions/duree`, demande, {
        headers: { 'x-api-password': GATEWAY_PASSWORD },
      })
      .pipe(map((r) => r.reponse));
  }
}