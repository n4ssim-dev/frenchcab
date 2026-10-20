import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { NouvelleReservation } from './nouvelle-reservation';

describe('NouvelleReservation', () => {
  let component: NouvelleReservation;
  let fixture: ComponentFixture<NouvelleReservation>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NouvelleReservation],
      providers: [provideRouter([])],
    }).compileComponents();

    fixture = TestBed.createComponent(NouvelleReservation);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('pré-remplit le formulaire depuis les query params', () => {
    fixture.componentRef.setInput('depart', '132');
    fixture.componentRef.setInput('arrivee', '161');
    fixture.componentRef.setInput('duree', '35');
    expect(component.depart()).toBe(132);
    expect(component.arrivee()).toBe(161);
    expect(component.duree()).toBe(35);
  });

  it("ne réserve pas sans durée (la prédiction n'est pas obligatoire mais la durée oui)", () => {
    component.depart.set(132);
    component.arrivee.set(161);
    component.duree.set(null);
    component.reserver();
    expect(component.erreur()).toBeTruthy();
    expect(component.chargement()).toBe(false);
  });
});
