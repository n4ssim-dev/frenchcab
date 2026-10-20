import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { Prediction } from './prediction';

describe('Prediction', () => {
  let component: Prediction;
  let fixture: ComponentFixture<Prediction>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Prediction],
      providers: [provideRouter([])],
    }).compileComponents();

    fixture = TestBed.createComponent(Prediction);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
