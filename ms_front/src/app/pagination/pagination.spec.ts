import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Pagination } from './pagination';

describe('Pagination', () => {
  let component: Pagination;
  let fixture: ComponentFixture<Pagination>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Pagination],
    }).compileComponents();

    fixture = TestBed.createComponent(Pagination);
    component = fixture.componentInstance;
    fixture.componentRef.setInput('nbPages', 3);
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('reste dans les bornes', () => {
    component.precedent();
    expect(component.page()).toBe(0);
    component.suivant();
    component.suivant();
    component.suivant();
    expect(component.page()).toBe(2);
  });

  it('revient à la première page quand la taille change', () => {
    component.page.set(2);
    component.changerTaille('50');
    expect(component.taille()).toBe(50);
    expect(component.page()).toBe(0);
  });
});
