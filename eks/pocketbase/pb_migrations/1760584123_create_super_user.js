/// <reference path="../pb_data/types.d.ts" />
/**
 * Adds the rk_admin@reknew.ai superuser account
 */
migrate((app) => {
  console.log("Setting up Admin account...");

  let superusers = app.findCollectionByNameOrId("_superusers")

  let record = new Record(superusers)

  // note: the values can be eventually loaded via $os.getenv(key)
  // or from a special local config file
  record.set("email", "admin@gmail.com")
  record.set("password", "Admin@1234")

  app.save(record)
  console.log("Set up Admin account successfully!")
}, (app) => { // optional revert operation
  try {
      console.log("Deleting Admin account...");
      let record = app.findAuthRecordByEmail("_superusers", "admin@gmail.com")
      app.delete(record)
      console.log("Deleted Admin account successfully!");
  } catch (e) {
      // silent errors (probably already deleted)
      console.log("Failed deleting Admin account!", e);
  }
})