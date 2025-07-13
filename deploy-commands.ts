import { REST, Routes } from "discord.js";
import { commands } from "./ts-commands";
import { readFileSync } from 'fs';

const commandsData = Object.values(commands).map((command) => command.data);

const rest = new REST({ version: "10" }).setToken(readFileSync('/home/interrobang/VALUABLE/dimmy_widderkins_token.txt', 'utf-8').trim());

type DeployCommandsProps = {
  guildId: string;
};

export async function deployCommands({ guildId }: DeployCommandsProps) {
  try {
    console.log("Started refreshing application (/) commands.");

    await rest.put(
      Routes.applicationGuildCommands("1330727173115613304", guildId),
      {
        body: commandsData,
      }
    );

    console.log("Successfully reloaded application (/) commands.");
  } catch (error) {
    console.error(error);
  }
}


