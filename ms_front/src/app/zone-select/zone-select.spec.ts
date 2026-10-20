import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ZoneSelect } from './zone-select';

describe('ZoneSelect', () => {
  let component: ZoneSelect;
  let fixture: ComponentFixture<ZoneSelect>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ZoneSelect],
    }).compileComponents();

    fixture = TestBed.createComponent(ZoneSelect);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('convertit la valeur choisie en identifiant numérique', () => {
    component.choisir('132');
    expect(component.valeur()).toBe(132);
    component.choisir('');
    expect(component.valeur()).toBeNull();
  });
});
