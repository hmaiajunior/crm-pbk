import { api } from "./api";

export interface Operador {
  id: string;
  nome: string;
  email: string;
}

export interface LoginResponse {
  token: string;
  operador: Operador;
}

export const authService = {
  login: (email: string, senha: string) =>
    api.post<LoginResponse>("/auth/login", { email, senha }),
};
