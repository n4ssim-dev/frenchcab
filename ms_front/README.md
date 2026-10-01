# MsFront

This project was generated using [Angular CLI](https://github.com/angular/angular-cli) version 22.0.3.

## Development server

To start a local development server, run:

```bash
ng serve
```

Once the server is running, open your browser and navigate to `http://localhost:4200/`. The application will automatically reload whenever you modify any of the source files.

## Code scaffolding

Angular CLI includes powerful code scaffolding tools. To generate a new component, run:

```bash
ng generate component component-name
```

For a complete list of available schematics (such as `components`, `directives`, or `pipes`), run:

```bash
ng generate --help
```

## Building

To build the project run:

```bash
ng build
```

This will compile your project and store the build artifacts in the `dist/` directory. By default, the production build optimizes your application for performance and speed.

## Running unit tests

To execute unit tests with the [Vitest](https://vitest.dev/) test runner, use the following command:

```bash
ng test
```

## Running end-to-end tests

For end-to-end (e2e) testing, run:

```bash
ng e2e
```

Angular CLI does not come with an end-to-end testing framework by default. You can choose one that suits your needs.

## Additional Resources

For more information on using the Angular CLI, including detailed command references, visit the [Angular CLI Overview and Command Reference](https://angular.dev/tools/cli) page.

Si depuis ton navigateur, la VM (20.19.124.235) ne répond pas sur les ports 4200 et 8000 (ERR_CONNECTION_TIMED_OUT) : le pare-feu de la VM ne laisse passer que le SSH. Les services tournent pourtant bien, puisque curl http://localhost:8000/docs répond 200 depuis la VM.

## Accéder à FrenchCab sur la VM : pare-feu et tunnel SSH

Pour y accéder malgré tout, on utilise un tunnel SSH, ouvre un terminal vierge et tape:
ssh -L 4200:localhost:4200 -L 3000:localhost:3000 groupe3@20.19.124.235

Puis rentre le mdp du SSH.

Ensuite ouvre http://localhost:4200. La solution durable c'est d'ouvrir le port 4200 (et le 3000 pour le gateway) dans le pare-feu. 
 
 Attention il ne faut pas exposer le 8000, dont les routes /donnees/* n'ont pas d'authentification.
