import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { CoursesService } from '../courses.service';
import { Prediction } from './prediction';

const MODELE_FACTICE = {
  nom_modele: 'Random Forest',
  algorithme: 'RandomForestRegressor',
  version: 'a1b2c3d4',
  empreinte_md5: 'a1b2c3d4e5f60718293a4b5c6d7e8f90',
  fichier: 'model_duree_premier.joblib',
  date_fichier: '2026-10-19T13:14:00',
  nombre_variables: 12,
  metriques: { mae_minutes: 3.39 },
};

describe('Prediction', () => {
  let component: Prediction;
  let fixture: ComponentFixture<Prediction>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Prediction],
      providers: [
        provideRouter([]),
        {
          provide: CoursesService,
          useValue: {
            getModele: () => of(MODELE_FACTICE),
            predireDuree: () => of({ duree_predite_min: 10 }),
          },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(Prediction);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('affiche le nom et la version du modèle utilisé', async () => {
    await fixture.whenStable();
    const texte = fixture.nativeElement.textContent;
    expect(texte).toContain('Random Forest');
    expect(texte).toContain('a1b2c3d4');
  });
});
