import { useEffect, useState } from "react";
import type { ComponentType } from "react";
import Bug1 from "./bugs/Bug1";
import Bug2 from "./bugs/Bug2";
import Bug3 from "./bugs/Bug3";

const ROUTES: Record<string, ComponentType> = {
  "#/bug1": Bug1,
  "#/bug2": Bug2,
  "#/bug3": Bug3,
};

export default function App() {
  const [hash, setHash] = useState(window.location.hash || "#/bug1");

  useEffect(() => {
    const onChange = () => setHash(window.location.hash || "#/bug1");
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);

  const Page = ROUTES[hash] ?? Bug1;
  return <Page />;
}
